import time
import traceback
from datetime import datetime

from ..agent.loop import AgentLoop, RunResult
from ..agent.tools import register_tools
from ..agent.intent_router import classify, route, IntentType
from ..agent.task_decomposer import decompose, aggregate_results
from ..agent.escalation import EscalationManager, Strategy
from ..agent.recovery import RecoveryManager
from ..agent.sub_agent import create_with_role, run_sub_agent
from ..agent.reviewer import run_review, parse_review_verdict, run_review_loop
from ..config import ZsigaConfig
from ..intake.scanner import DirectoryScanner
from .. import git_ops
from ..memory.context import load_active_context, update_active_context, load_recent_lessons
from ..memory.learn import record_outcome, record_lesson
from ..metrics.types import ChangeRecord, PhaseRecord, Phase, Outcome
from ..metrics.db import record_self_assessment, query_recent_ratings
from ..metrics.collector import record_change
from ..metrics.intent_tracker import record_intent_decision, update_intent_outcome, update_intent_reclassification
from ..memory.journal import export_session
from ..transport import Transport, create_transport
from .enricher import enrich, derive_explore_tasks
from .clarifier import clarify
from .optimizer import optimize as run_optimize
from .implementer import implement
from .verifier import verify, read_verdict
from .diagnoser import Diagnoser
from .phase_wal import PhaseWAL
from .utils import verify_mechanical, archive_change, _get_changed_files, read_file, resolve_venv_python
from .github_issue import create_issue, extract_github_repo
from .project_context import build_project_context, prefetch_mechanical


class ZsigaOrchestrator:

    def __init__(self, config: ZsigaConfig):
        self.config = config
        self.agent = AgentLoop(
            config.llm.api_key,
            config.llm.model,
            base_url=config.llm.base_url,
            proxy=config.llm.proxy,
            compaction_enabled=config.pipeline.compaction.enabled,
            compaction_threshold=config.pipeline.compaction.threshold_chars,
            compaction_keep_recent=config.pipeline.compaction.keep_recent,
        )
        self._transports: dict[str, Transport] = {}
        self._load_context()

    def _get_transport(self, project_name: str) -> Transport:
        if project_name not in self._transports:
            target_config = self.config.targets[project_name]
            self._transports[project_name] = create_transport(target_config)
        return self._transports[project_name]

    def _load_context(self):
        ctx = load_active_context()
        if ctx:
            self.agent.context = ctx
            print(f"  📝 Loaded memory context ({len(ctx)} chars)")

    async def run_cycle(self):
        for name in self.config.targets:
            self._get_transport(name)
        scanner = DirectoryScanner(self.config.targets)
        proposals = scanner.scan(transports=self._transports)

        print(f"\n{'='*60}")
        print(f"zsiga cycle: found {len(proposals)} active changes")
        print(f"{'='*60}")

        processed = 0
        for prop in proposals:
            if processed >= self.config.pipeline.max_changes_per_cycle:
                break

            print(f"\n--- {prop['id']} ({prop['project']}) ---")

            try:
                # Cross-project decomposition (REQ-TD-01)
                available_projects = list(self.config.targets.keys())
                proposal_text = read_file(
                    f"{prop['change_dir']}/{prop.get('proposal_filename', 'proposal.md')}",
                    self._get_transport(prop['project']),
                ) or ""
                decomp = decompose(proposal_text, available_projects,
                                   originating_project=prop['project'])

                if len(decomp.subtasks) > 1:
                    print(f"  Cross-project: {len(decomp.subtasks)} subtasks detected")

                    # Decompose post-validation: verify change_dir exists on each subtask's transport
                    invalid_subtasks = []
                    for subtask in decomp.subtasks:
                        target_cfg = self.config.targets.get(subtask.project)
                        if not target_cfg:
                            invalid_subtasks.append(subtask)
                            continue
                        sub_transport = self._get_transport(subtask.project)
                        r = sub_transport.run_shell(
                            f"test -d '{prop['change_dir']}'",
                            timeout=10,
                        )
                        if r["exit_code"] != 0:
                            invalid_subtasks.append(subtask)

                    if invalid_subtasks:
                        # Record lesson and downgrade to originating project only
                        record_outcome(
                            prop["id"], prop["project"], False, "decompose",
                            detail="decompose returned false positive: change_dir missing on remote",
                            error_domain="pipeline",
                            root_cause="decompose.false_positive",
                            prevention="Validate cross-project change_dir existence before decomposing",
                        )
                        print(
                            f"  ⚠ Decompose downgrade: {len(invalid_subtasks)} invalid subtask(s), "
                            f"falling back to single-project"
                        )
                        # Fall through to single-project processing below
                    else:
                        # All subtasks validated — proceed with cross-project decomposition
                        results = {}
                        for subtask in decomp.subtasks:
                            target_cfg = self.config.targets.get(subtask.project)
                            if not target_cfg:
                                results[subtask.project] = {
                                    "status": "fail",
                                    "detail": "project not configured",
                                }
                                continue
                            sub_prop = dict(prop)
                            sub_prop["project"] = subtask.project
                            sub_prop["target_path"] = target_cfg.path
                            self._get_transport(subtask.project)
                            success = await self._process_change(sub_prop)
                            results[subtask.project] = {
                                "status": "pass" if success else "fail",
                            }

                        summary = aggregate_results(results)
                        print(
                            f"  Decomposition summary: "
                            f"{summary['passed']}/{summary['total']} passed"
                        )
                        record_lesson(
                            title=f"Cross-project: {prop['id']}",
                            context=f"subtasks={len(decomp.subtasks)}",
                            takeaway=f"Results: {summary['passed']}/{summary['total']} passed",
                            pattern_key="pipeline.cross_project",
                            source="decomposer",
                        )
                        processed += 1
                        continue  # skip single-project processing below

                    # Downgraded: fall through to single-project processing
                else:
                    if await self._process_change(prop):
                        processed += 1
            except Exception as exc:
                tb = traceback.format_exc()
                print(f"❌ Proposal {prop['id']} failed: {exc}\n{tb}")
                record_lesson(
                    title=f"Proposal error: {prop['id']}",
                    context=f"type={type(exc).__name__}, tb={tb[:500]}",
                    takeaway=f"{type(exc).__name__}: {exc}",
                    pattern_key="daemon.cycle_error",
                    source="orchestrator",
                )
                continue

        self._update_memory()

        print(f"\n{'='*60}")
        print(f"Cycle complete: {processed} changes processed")
        print(f"{'='*60}")

        return processed

    def _update_memory(self):
        lessons = load_recent_lessons(n=20)
        if lessons:
            update_active_context(new_lessons=lessons)
            print(f"  📝 Memory updated with {len(lessons)} recent lessons")

    async def _process_change(self, prop: dict) -> bool:
        change_dir = prop["change_dir"]
        target_path = prop["target_path"]
        project_name = prop["project"]
        project_config = self.config.targets[project_name]
        change_name = prop["id"]
        transport = self._get_transport(project_name)

        # Intent classification (REQ-IG-01 / REQ-IG-02 / REQ-IG-05)
        proposal_name = prop.get("proposal_filename", "proposal.md")
        proposal_text = read_file(f"{change_dir}/{proposal_name}", transport) or ""
        if not proposal_text.strip():
            print(f"  ⚠ Empty proposal for {change_name} on {project_name} — skipping")
            return False
        intent = classify(proposal_text, source="openspec")
        route_path = route(intent)
        print(
            f"  Intent: {intent.intent_type.value} "
            f"(confidence={intent.confidence:.2f}, route={route_path})"
        )
        # REQ-IG-05: Log verbalization, category, confidence, route
        print(
            f"  Verbalization: {intent.verbalization}"
        )

        # Record intent decision for accuracy tracking
        intent_row_id = record_intent_decision(
            change_name=change_name,
            project=project_name,
            predicted_intent=intent.intent_type.value,
            confidence=intent.confidence,
            classification_source="openspec_override",
            verbalization=intent.verbalization,
            reasoning=intent.reasoning,
        )

        # Confidence gate: low-confidence non-OPEN_ENDED triggers explore-then-reclassify
        if intent.confidence < 0.6 and intent.intent_type != IntentType.OPEN_ENDED:
            print(f"  Confidence gate: {intent.confidence:.2f} < 0.6, dispatching explore for context")
            try:
                from ..agent.sub_agent import create_with_role as _create_role
                from ..agent.sub_agent import run_sub_agent as _run_sub
                explore_agent = _create_role(
                    "explore",
                    api_key=self.agent.client.api_key,
                    model=self.agent.model,
                    base_url=getattr(self.agent.client, "base_url", None),
                )
                explore_result = await _run_sub(
                    explore_agent, target_path, transport, proposal_text,
                    max_turns=10, timeout_seconds=120,
                )
                if explore_result.success and explore_result.content.strip():
                    enriched_text = proposal_text + "\n\n## Supplementary Context\n" + explore_result.content
                    new_intent = classify(enriched_text, source="openspec")
                    if new_intent.intent_type != intent.intent_type or new_intent.confidence > intent.confidence:
                        print(
                            f"  Reclassified: {intent.intent_type.value} → {new_intent.intent_type.value} "
                            f"(confidence {intent.confidence:.2f} → {new_intent.confidence:.2f})"
                        )
                        update_intent_reclassification(
                            row_id=intent_row_id,
                            reclassified_from=intent.intent_type.value,
                            reclassified_to=new_intent.intent_type.value,
                        )
                        intent = new_intent
                        route_path = route(intent)
            except Exception as gate_err:
                print(f"  Confidence gate explore failed: {gate_err}, using original classification")

        if route_path == "ask_user":
            print(f"  Intent unclear, asking user for clarification: {intent.verbalization}")
            update_intent_outcome(change_name, "routed", True)
            return False

        if route_path == "dispatch_explore":
            print("  Dispatching explore sub-agent for research intent")
            explore_ok = await self._dispatch_explore(prop, change_dir, target_path, transport)
            update_intent_outcome(change_name, "success" if explore_ok else "failed", explore_ok)
            return explore_ok

        if route_path == "dispatch_diagnoser":
            print("  Dispatching diagnoser sub-agent for investigation intent")
            diag_ok = await self._dispatch_diagnoser(prop, change_dir, target_path, transport)
            update_intent_outcome(change_name, "success" if diag_ok else "failed", diag_ok)
            return diag_ok

        if route_path == "dispatch_review":
            print("  Dispatching review sub-agent for evaluation intent")
            review_ok = await self._dispatch_review(prop, change_dir, target_path, transport)
            update_intent_outcome(change_name, "success" if review_ok else "failed", review_ok)
            return review_ok

        if route_path == "pipeline_fix":
            print("  Running shortened pipeline (IMPLEMENT → VERIFY) for fix intent")

        # IMPLEMENTATION and FIX intents proceed to pipeline
        if intent.intent_type not in (IntentType.IMPLEMENTATION, IntentType.FIX):
            print(f"  Skipping non-pipeline intent: {route_path}")
            update_intent_outcome(change_name, "routed", True)
            return False

        rec = ChangeRecord(
            change_name=change_name,
            project=project_name,
            outcome=Outcome.SUCCESS,
            started_at=datetime.now().isoformat(),
        )

        try:
            skip_enrich = intent.intent_type == IntentType.FIX
            return await self._run_phases(prop, rec, change_dir, target_path,
                                          project_name, project_config, change_name,
                                          transport, skip_enrich=skip_enrich,
                                          intent=intent)
        finally:
            record_change(rec)
            export_session(change_name)
            # Update intent accuracy outcome based on pipeline result
            if rec.outcome == Outcome.SUCCESS:
                update_intent_outcome(change_name, "success", True)
            elif rec.outcome == Outcome.REVERTED:
                update_intent_outcome(change_name, "reverted", False)
            else:
                update_intent_outcome(change_name, "skipped", True)

            # Cleanup: ensure working tree is clean for next proposal.
            # IMPORTANT: reset_hard BEFORE checkout. Otherwise the daemon's own
            # runtime writes (data/daemon.log, daemon_state.json, lock.pid, ...)
            # leave the tree dirty and `git checkout` aborts, which would carry
            # stale phase artifacts into the next proposal.
            try:
                deploy_branch = project_config.deploy_branch
                if git_ops.has_uncommitted_changes(target_path, transport=transport):
                    print(
                        "  Post-proposal cleanup: reset_hard to discard runtime dirt",
                        flush=True,
                    )
                    git_ops.reset_hard(
                        target_path,
                        git_ops.rev_parse(target_path, transport=transport),
                        transport=transport,
                    )
                current = git_ops.current_branch(target_path, transport=transport)
                if current != deploy_branch:
                    git_ops.checkout(target_path, deploy_branch, transport=transport)
                # Belt-and-suspenders: after the checkout, the new branch may
                # still expose untracked daemon artifacts.
                if git_ops.has_uncommitted_changes(target_path, transport=transport):
                    git_ops.reset_hard(
                        target_path,
                        git_ops.rev_parse(target_path, transport=transport),
                        transport=transport,
                    )
            except Exception as cleanup_err:
                print(f"  ⚠ Cleanup warning: {cleanup_err}", flush=True)

    async def _run_phases(self, prop, rec, change_dir, target_path,
                          project_name, project_config, change_name,
                          transport: Transport,
                          skip_enrich: bool = False,
                          intent: object = None) -> bool:
        cycle_start = time.monotonic()

        # Phase WAL for crash recovery
        wal = PhaseWAL(change_dir, transport)

        # Escalation manager (REQ-ES-01)
        escalation = EscalationManager(change_name, persist_dir=change_dir)

        # Resolve venv python path once for all phases
        venv_python = resolve_venv_python(target_path, project_config, transport)
        if venv_python:
            print(f"  venv python: {venv_python}")

        # Prefetch project context once (shared by enrich + implement)
        print("  Prefetching project context...")
        t_pf = time.monotonic()
        proposal_name = prop.get("proposal_filename", "proposal.md")
        proposal_text = read_file(f"{change_dir}/{proposal_name}", transport) or ""
        project_context = build_project_context(target_path, transport,
                                                 proposal=proposal_text)
        print(f"  Project context ready ({len(project_context)} chars, {time.monotonic() - t_pf:.1f}s)")

        # Phase 0: CLARIFY (requirement engineering — skipped for FIX intent)
        if not skip_enrich:
            print(f"\n  {'='*50}")
            print(f"  Phase 0/6: CLARIFY {change_name}")
            print(f"  {'='*50}")
            self.agent.set_phase("clarify")
            register_tools(self.agent, target_path, transport=transport)
            t0 = time.monotonic()

            # Optional parallel explore pool for CLARIFY
            supplementary_context = ""
            if self.config.pipeline.enrich_parallel_explore:
                from ..agent.sub_agent import dispatch_many, collect_all
                explore_tasks = derive_explore_tasks(proposal_text)
                pool_cfg = self.config.pipeline
                handle = dispatch_many(
                    tasks=explore_tasks,
                    api_key=self.config.llm.api_key,
                    model=self.config.llm.model,
                    base_url=self.config.llm.base_url,
                    proxy=self.config.llm.proxy,
                    target_path=target_path,
                    transport=transport,
                    max_concurrency=pool_cfg.explore_pool_max_concurrency,
                    max_turns_per_task=pool_cfg.explore_pool_max_turns,
                    timeout_per_task=pool_cfg.explore_pool_timeout,
                )
                explore_results = await collect_all(handle)
                parts = []
                for idx, r in enumerate(explore_results):
                    if r.success:
                        parts.append(
                            f"### Explore Agent #{idx + 1}\n{r.content}"
                        )
                    else:
                        print(
                            f"  ⚠️ explore-agent #{idx + 1} failed: "
                            f"{r.content[:100]}"
                        )
                if parts:
                    supplementary_context = "\n\n".join(parts)

            clarify_result = await clarify(
                self.agent, change_dir, target_path,
                transport=transport,
                project_context=project_context,
                supplementary_context=supplementary_context,
                max_turns=3, timeout_seconds=120,
            )
            clarify_calls = _extract_calls(clarify_result)
            clarify_tokens = _extract_tokens(clarify_result)
            rec.phases.append(PhaseRecord(
                phase=Phase.CLARIFY, outcome=Outcome.SUCCESS,
                seconds_used=time.monotonic() - t0,
                llm_calls=clarify_calls[0], tool_calls=clarify_calls[1],
                prompt_tokens=clarify_tokens[0], completion_tokens=clarify_tokens[1],
            ))
            print(f"  Phase 0 done in {time.monotonic() - t0:.1f}s")

        # Phase 1: ENRICH (skipped for pipeline_fix — FIX intent)
        if not skip_enrich and not (prop["has_specs"] and prop["has_design"] and prop["has_tasks"]):
            print(f"\n  {'='*50}")
            print(f"  Phase 1/6: ENRICH {change_name}")
            print(f"  {'='*50}")
            self.agent.set_phase("enrich")
            register_tools(self.agent, target_path, transport=transport)
            t0 = time.monotonic()

            # Optional parallel explore pool (REQ-PP-04)
            supplementary_context = ""
            if self.config.pipeline.enrich_parallel_explore:
                from ..agent.sub_agent import dispatch_many, collect_all
                explore_tasks = derive_explore_tasks(proposal_text)
                pool_cfg = self.config.pipeline
                handle = dispatch_many(
                    tasks=explore_tasks,
                    api_key=self.config.llm.api_key,
                    model=self.config.llm.model,
                    base_url=self.config.llm.base_url,
                    proxy=self.config.llm.proxy,
                    target_path=target_path,
                    transport=transport,
                    max_concurrency=pool_cfg.explore_pool_max_concurrency,
                    max_turns_per_task=pool_cfg.explore_pool_max_turns,
                    timeout_per_task=pool_cfg.explore_pool_timeout,
                )
                explore_results = await collect_all(handle)
                parts = []
                for idx, r in enumerate(explore_results):
                    if r.success:
                        parts.append(
                            f"### Explore Agent #{idx + 1}\n{r.content}"
                        )
                    else:
                        print(
                            f"  ⚠️ explore-agent #{idx + 1} failed: "
                            f"{r.content[:100]}"
                        )
                if parts:
                    supplementary_context = "\n\n".join(parts)

            enrich_result = await enrich(self.agent, change_dir, target_path,
                        transport=transport,
                        project_context=project_context,
                        supplementary_context=supplementary_context,
                        max_turns=self.config.pipeline.enrich_max_turns,
                         timeout_seconds=self.config.pipeline.enrich_timeout)
            enrich_calls = _extract_calls(enrich_result)
            enrich_tokens = _extract_tokens(enrich_result)
            rec.phases.append(PhaseRecord(
                phase=Phase.ENRICH, outcome=Outcome.SUCCESS,
                seconds_used=time.monotonic() - t0,
                llm_calls=enrich_calls[0], tool_calls=enrich_calls[1],
                prompt_tokens=enrich_tokens[0], completion_tokens=enrich_tokens[1],
            ))
            print(f"  Phase 1 done in {time.monotonic() - t0:.1f}s")

            # WAL: record ENRICH boundary
            wal.write(phase="enrich", target_path=target_path, project=project_name)

        # Approval gate
        if self.config.safety.require_approval:
            approved = self._ask_approval(change_name)
            if not approved:
                print("  Skipped: not approved")
                rec.outcome = Outcome.SKIPPED
                return False

        # Phase 2: IMPLEMENT
        print(f"\n  {'='*50}")
        print(f"  Phase 2/6: IMPLEMENT {change_name}")
        print(f"  {'='*50}")
        self.agent.set_phase("impl")

        # Feature branch isolation: ensure on zsiga/<change_name>
        deploy_branch = project_config.deploy_branch
        feature_branch = f"zsiga/{change_name}"
        # Pre-checkout cleanup (P2 fix): if working tree is dirty (e.g. zsiga.db /
        # learnings.jsonl modified by CLARIFY/ENRICH), commit it BEFORE switching
        # branches, otherwise `git checkout` aborts and the proposal fails.
        if git_ops.has_uncommitted_changes(target_path, transport=transport):
            print("  Pre-checkout cleanup: committing dirty working tree", flush=True)
            git_ops.add_all(target_path, transport=transport)
            git_ops.commit(target_path,
                          f"zsiga: pre-checkout cleanup for {change_name}",
                          transport=transport)
        if git_ops.branch_exists(target_path, feature_branch, transport=transport):
            git_ops.checkout(target_path, feature_branch, transport=transport)
            print(f"  Checked out existing feature branch: {feature_branch}")
        else:
            git_ops.create_branch(target_path, feature_branch, transport=transport)
            print(f"  Created feature branch: {feature_branch}")

        # Pre-flight checkpoint: commit dirty tree on the feature branch
        # (covers the case where checkout itself surfaced new untracked files).
        if git_ops.has_uncommitted_changes(target_path, transport=transport):
            git_ops.add_all(target_path, transport=transport)
            git_ops.commit(target_path, f"zsiga: checkpoint before {change_name}",
                          transport=transport)
        pre_sha = git_ops.rev_parse(target_path, transport=transport)
        print(f"  Pre-impl SHA: {pre_sha}")

        # Recovery manager (REQ-RI-01)
        recovery = RecoveryManager(
            change_name, target_path=target_path, pre_sha=pre_sha,
            transport=transport, persist_dir=change_dir,
        )
        register_tools(self.agent, target_path, transport=transport)
        t0 = time.monotonic()
        impl_result = await implement(self.agent, change_dir, target_path,
                       transport=transport,
                       project_context=project_context,
                       venv_python=venv_python,
                       max_turns=self.config.pipeline.impl_max_turns,
                        timeout_seconds=self.config.pipeline.impl_timeout)
        impl_seconds = time.monotonic() - t0
        impl_calls = _extract_calls(impl_result)
        impl_tokens = _extract_tokens(impl_result)
        print(f"  Phase 2 done in {impl_seconds:.1f}s")

        # Checkpoint after IMPLEMENT: commit working tree so REVIEW/VERIFY can diff
        if git_ops.has_uncommitted_changes(target_path, transport=transport):
            git_ops.add_all(target_path, transport=transport)
            git_ops.commit(target_path, f"zsiga: implement {change_name}",
                          transport=transport)
            print("  Post-impl checkpoint committed")

        # Mechanical verification (only check changed files)
        print("\n  Mechanical verification...")
        fix_attempts = 0
        t_mv = time.monotonic()
        passed, errors = verify_mechanical(
            target_path, project_config.test_cmd, project_config.lint_cmd,
            since_sha=pre_sha, transport=transport,
        )
        mv_seconds = time.monotonic() - t_mv
        if passed:
            print(f"  Mechanical verification PASSED ({mv_seconds:.1f}s)")
        else:
            print(f"  Mechanical verification FAILED ({mv_seconds:.1f}s)")
            print(f"  Errors: {errors[:300]}")
            print("  Attempting fixes...")
            fixed, fix_attempts = await self._fix_loop(
                target_path, project_config,
                errors, pre_sha=pre_sha, transport=transport,
                max_attempts=self.config.pipeline.fix_attempts,
                venv_python=venv_python,
                escalation=escalation,
                recovery=recovery,
            )
            if not fixed:
                # Escalation abort check (REQ-ES-04)
                if escalation.should_abort():
                    self._handle_escalation_abort(
                        escalation, change_dir, change_name,
                        project_name, transport,
                        recovery=recovery,
                    )

                git_ops.reset_hard(target_path, pre_sha, transport=transport)
                print(f"  REVERTED: {change_name}")
                rec.outcome = Outcome.REVERTED
                rec.phases.append(PhaseRecord(
                    phase=Phase.IMPLEMENT, outcome=Outcome.FAIL,
                    seconds_used=impl_seconds, fix_attempts=fix_attempts, detail=errors[:200],
                    llm_calls=impl_calls[0], tool_calls=impl_calls[1],
                    prompt_tokens=impl_tokens[0], completion_tokens=impl_tokens[1],
                ))
                record_outcome(change_name, project_name, False, "implement", errors)
                return False

        rec.phases.append(PhaseRecord(
            phase=Phase.IMPLEMENT, outcome=Outcome.SUCCESS,
            seconds_used=impl_seconds, fix_attempts=fix_attempts,
            llm_calls=impl_calls[0], tool_calls=impl_calls[1],
            prompt_tokens=impl_tokens[0], completion_tokens=impl_tokens[1],
        ))

        # Phase 3/6: REVIEW (self-review loop)
        if self.config.pipeline.review_max_rounds > 0:
            print(f"\n  {'='*50}", flush=True)
            print(f"  Phase 3/6: REVIEW {change_name}", flush=True)
            print(f"  {'='*50}", flush=True)
            t_review = time.monotonic()
            # Hard ceiling around the entire review loop so the daemon can never
            # hang forever even if an inner timeout misbehaves.
            review_loop_ceiling = max(
                900,
                int(getattr(self.config.pipeline, "review_timeout", 180))
                * max(1, getattr(self.config.pipeline, "review_max_rounds", 1))
                * 3,
            )
            print(f"  [ORCH] review_loop_ceiling={review_loop_ceiling}s", flush=True)
            try:
                import asyncio as _asyncio
                review_result = await _asyncio.wait_for(
                    run_review_loop(
                        self.agent, change_dir, target_path, pre_sha, transport,
                        max_rounds=self.config.pipeline.review_max_rounds,
                        review_max_turns=self.config.pipeline.review_max_turns,
                        review_timeout=self.config.pipeline.review_timeout,
                        fix_max_turns=self.config.pipeline.review_fix_max_turns,
                    ),
                    timeout=review_loop_ceiling,
                )
            except _asyncio.TimeoutError:
                review_seconds = time.monotonic() - t_review
                print(
                    f"  [ORCH] ⏱️ REVIEW HARD-CEILING after {review_seconds:.1f}s "
                    f"(ceiling={review_loop_ceiling}s) — recording UNKNOWN and moving on",
                    flush=True,
                )
                from ..agent.reviewer import ReviewLoopResult as _RLR
                review_result = _RLR(
                    final_verdict="UNKNOWN",
                    rounds_executed=0,
                    fix_attempts=0,
                    elapsed_seconds=review_seconds,
                    last_issues=[],
                    had_critical=False,
                )
            except Exception as _exc:  # pragma: no cover - defensive
                review_seconds = time.monotonic() - t_review
                print(
                    f"  [ORCH] ❌ REVIEW raised {_exc.__class__.__name__}: {_exc} "
                    f"after {review_seconds:.1f}s — recording UNKNOWN",
                    flush=True,
                )
                from ..agent.reviewer import ReviewLoopResult as _RLR
                review_result = _RLR(
                    final_verdict="UNKNOWN",
                    rounds_executed=0,
                    fix_attempts=0,
                    elapsed_seconds=review_seconds,
                    last_issues=[],
                    had_critical=False,
                )
            review_seconds = time.monotonic() - t_review
            review_outcome = (
                Outcome.SUCCESS
                if review_result.final_verdict == "CLEAN"
                else Outcome.FAIL
            )
            print(
                f"  Review: verdict={review_result.final_verdict} "
                f"rounds={review_result.rounds_executed} "
                f"fixes={review_result.fix_attempts} ({review_seconds:.1f}s)"
            )
            rec.phases.append(PhaseRecord(
                phase=Phase.REVIEW, outcome=review_outcome,
                seconds_used=review_seconds,
                fix_attempts=review_result.fix_attempts,
                detail=_summarize_issues(review_result.last_issues),
                llm_calls=review_result.llm_calls,
                tool_calls=review_result.tool_calls,
                prompt_tokens=review_result.prompt_tokens,
                completion_tokens=review_result.completion_tokens,
            ))

            # Record lesson for critical review issues (REQ-RL-01)
            if review_result.had_critical:
                critical_issues = [
                    i for i in review_result.last_issues
                    if i.get("severity") == "CRITICAL"
                ]
                issue_summary = "; ".join(
                    i.get("description", "")[:80] for i in critical_issues
                )[:200]
                record_lesson(
                    title=f"REVIEW CRITICAL: {change_name}",
                    context=f"project={project_name}, rounds={review_result.rounds_executed}",
                    takeaway=f"Review found critical issues: {issue_summary}",
                    pattern_key="pipeline.review.critical",
                    source="reviewer",
                )

        # Phase 3: VERIFY
        print(f"\n  {'='*50}")
        print(f"  Phase 4/6: VERIFY {change_name}")
        print(f"  {'='*50}")
        self.agent.set_phase("verify")
        register_tools(self.agent, target_path, transport=transport)

        # Verify pre-check: lightweight import + lint on changed files
        from .diagnoser import verify_precheck as _verify_precheck
        changed_for_precheck = _get_changed_files(target_path, pre_sha, transport)
        precheck_result = _verify_precheck(target_path, changed_for_precheck, transport)

        print("  Prefetching test/lint results...")
        t_mech = time.monotonic()
        mech_results = prefetch_mechanical(
            target_path, project_config.test_cmd, project_config.lint_cmd,
            since_sha=pre_sha,
            transport=transport,
        )
        print(f"  Test: {'✅' if mech_results['test']['passed'] else '❌'}, "
              f"Lint: {'✅' if mech_results['lint']['passed'] else '❌'} "
              f"({time.monotonic() - t_mech:.1f}s)")

        eval_fix_attempts = 0

        if not precheck_result.passed:
            print(
                f"  Pre-check FAILED: {precheck_result.error_type} "
                f"in {precheck_result.file_path}"
            )
            print(f"  {precheck_result.message[:300]}")
            print("  Skipping LLM verify, entering eval-fix loop directly")

            # Build synthetic verify.md with the pre-check error
            verify_content = (
                f"Verdict: FAIL\n\n"
                f"Pre-check failure ({precheck_result.error_type}):\n"
                f"{precheck_result.message}\n"
            )
            verify_path = f"{change_dir}/verify.md"
            transport.run_shell(
                f"cat > '{verify_path}' << 'ZSIGA_VERIFY_EOF'\n{verify_content}\nZSIGA_VERIFY_EOF",
                timeout=10,
            )

            verdict = "FAIL"
            verify_outcome = Outcome.FAIL
            verify_seconds = 0.0
            verify_calls = (0, 0)
            verify_tokens = (0, 0)

            # Enter eval-fix loop with the pre-check error
            print("  Attempting eval fixes for pre-check failure...")
            fixed, eval_fix_attempts = await self._eval_fix_loop(
                change_dir, target_path, project_config,
                pre_sha, transport=transport,
                max_attempts=self.config.pipeline.eval_fix_attempts,
                venv_python=venv_python,
                escalation=escalation,
                recovery=recovery,
            )
            if not fixed:
                # Escalation abort check (REQ-ES-04)
                if escalation.should_abort():
                    self._handle_escalation_abort(
                        escalation, change_dir, change_name,
                        project_name, transport,
                        recovery=recovery,
                    )
                else:
                    # Run structured diagnosis with pre-check details
                    try:
                        self._run_diagnosis(
                            change_dir, target_path, change_name,
                            project_name, transport,
                            verify_feedback=precheck_result.message,
                        )
                    except Exception as diag_err:
                        print(f"  Diagnosis failed: {diag_err}")

                git_ops.reset_hard(target_path, pre_sha, transport=transport)
                print(f"  REVERTED: {change_name} (verify pre-check failed)")
                rec.outcome = Outcome.REVERTED
                rec.phases.append(PhaseRecord(
                    phase=Phase.VERIFY, outcome=Outcome.FAIL,
                    seconds_used=0.0, fix_attempts=eval_fix_attempts,
                    detail=f"pre-check: {precheck_result.error_type} in {precheck_result.file_path}",
                ))
                record_outcome(change_name, project_name, False, "verify")
                return False

            # Pre-check fix succeeded; re-verify to confirm
            self.agent.set_phase("verify")
            register_tools(self.agent, target_path, transport=transport)
            t0 = time.monotonic()
            verify_result = await verify(self.agent, change_dir, target_path, pre_sha,
                        transport=transport,
                        mech_results=mech_results,
                        max_turns=self.config.pipeline.verify_max_turns,
                        timeout_seconds=self.config.pipeline.verify_timeout)
            verify_seconds = time.monotonic() - t0
            verify_calls = _extract_calls(verify_result)
            verify_tokens = _extract_tokens(verify_result)
            verdict = read_verdict(change_dir, transport)
            verify_outcome = Outcome.SUCCESS if verdict == "PASS" else Outcome.FAIL
            print(f"  Post-fix verdict: {verdict} ({verify_seconds:.1f}s)")
        else:
            print("  Pre-check PASSED, proceeding with LLM verify")
            t0 = time.monotonic()
            verify_result = await verify(self.agent, change_dir, target_path, pre_sha,
                        transport=transport,
                        mech_results=mech_results,
                        max_turns=self.config.pipeline.verify_max_turns,
                        timeout_seconds=self.config.pipeline.verify_timeout)
            verify_seconds = time.monotonic() - t0
            verify_calls = _extract_calls(verify_result)
            verify_tokens = _extract_tokens(verify_result)

            verdict = read_verdict(change_dir, transport)
            print(f"  Verdict: {verdict} ({verify_seconds:.1f}s)")
            verify_outcome = Outcome.SUCCESS if verdict == "PASS" else Outcome.FAIL
            eval_fix_attempts = 0

        if verdict == "FAIL":
            print("  Verifier: FAIL, attempting eval fixes...")
            fixed, eval_fix_attempts = await self._eval_fix_loop(
                change_dir, target_path, project_config,
                pre_sha, transport=transport,
                max_attempts=self.config.pipeline.eval_fix_attempts,
                venv_python=venv_python,
                escalation=escalation,
                recovery=recovery,
            )
            if not fixed:
                # Escalation abort check (REQ-ES-04)
                if escalation.should_abort():
                    self._handle_escalation_abort(
                        escalation, change_dir, change_name,
                        project_name, transport,
                        recovery=recovery,
                    )
                else:
                    # Run structured diagnosis before reverting
                    try:
                        self._run_diagnosis(
                            change_dir, target_path, change_name,
                            project_name, transport,
                        )
                    except Exception as diag_err:
                        print(f"  Diagnosis failed: {diag_err}")

                git_ops.reset_hard(target_path, pre_sha, transport=transport)
                print(f"  REVERTED: {change_name} (verify failed)")
                rec.outcome = Outcome.REVERTED
                rec.phases.append(PhaseRecord(
                    phase=Phase.VERIFY, outcome=Outcome.FAIL,
                    seconds_used=verify_seconds, fix_attempts=eval_fix_attempts,
                    llm_calls=verify_calls[0], tool_calls=verify_calls[1],
                    prompt_tokens=verify_tokens[0], completion_tokens=verify_tokens[1],
                ))
                record_outcome(change_name, project_name, False, "verify")
                return False

        rec.phases.append(PhaseRecord(
            phase=Phase.VERIFY, outcome=verify_outcome,
            seconds_used=verify_seconds, fix_attempts=eval_fix_attempts,
            llm_calls=verify_calls[0], tool_calls=verify_calls[1],
            prompt_tokens=verify_tokens[0], completion_tokens=verify_tokens[1],
        ))

        # Phase 4.5/6: OPTIMIZE (optional norm alignment)
        if getattr(self.config.pipeline, "optimize_enabled", True):
            sep = "=" * 50
            print(f"\n  {sep}")
            print(f"  Phase 4.5/6: OPTIMIZE {change_name}")
            print(f"  {sep}")
            self.agent.set_phase("optimize")
            register_tools(self.agent, target_path, transport=transport)
            t_opt = time.monotonic()
            opt_result = await run_optimize(
                self.agent, change_dir, target_path, pre_sha,
                transport=transport,
                max_turns=5, timeout_seconds=180,
            )
            opt_seconds = time.monotonic() - t_opt
            opt_calls = _extract_calls(opt_result)
            opt_tokens = _extract_tokens(opt_result)
            is_noop = "NO_OPTIMIZATION_NEEDED" in (opt_result.content if hasattr(opt_result, "content") else "")
            opt_detail = "noop" if is_noop else "optimized"
            print(f"  OPTIMIZE: {opt_detail} ({opt_seconds:.1f}s)")
            rec.phases.append(PhaseRecord(
                phase=Phase.OPTIMIZE, outcome=Outcome.SUCCESS,
                seconds_used=opt_seconds,
                detail=opt_detail,
                llm_calls=opt_calls[0], tool_calls=opt_calls[1],
                prompt_tokens=opt_tokens[0], completion_tokens=opt_tokens[1],
            ))

        # Phase 5/6: REFLECT (self-assessment)
        task_type = "refactor"  # default
        if intent is not None:
            task_type = self._INTENT_TO_TASK_TYPE.get(
                getattr(intent, "intent_type", None), "refactor"
            )
        print(f"\n  {'='*50}")
        print(f"  Phase 5/6: REFLECT {change_name}")
        print(f"  {'='*50}")
        reflect_seconds = self.phase_reflect(
            rec, change_name, project_name, task_type,
            change_dir, transport,
        )
        print(f"  Self-rating: {self._get_last_rating(rec)} ({reflect_seconds:.1f}s)")

        # Phase 4: DELIVER
        print(f"\n  {'='*50}")
        print(f"  Phase 6/6: DELIVER {change_name}")
        print(f"  {'='*50}")
        t0 = time.monotonic()

        # GitHub Issue creation (REQ-GH-001)
        issue_number = None
        if (
            self.config.github
            and self.config.github.issue_integration
        ):
            issue_number = self._try_create_issue(
                target_path, transport, change_name, proposal_text,
            )

        if git_ops.has_uncommitted_changes(target_path, transport=transport):
            git_ops.add_all(target_path, transport=transport)
            msg = f"feat({project_name}): {change_name}"
            if issue_number:
                msg += f" (closes #{issue_number})"
            git_ops.commit(target_path, msg, transport=transport)
        git_ops.tag(target_path, f"zsiga-{change_name}", transport=transport)

        # Push feature branch, then merge into deploy branch
        if not self.config.safety.dry_run:
            try:
                git_ops.push(target_path, branch=feature_branch, transport=transport)
                git_ops.checkout(target_path, deploy_branch, transport=transport)
                git_ops.pull(target_path, branch=deploy_branch, transport=transport)
                git_ops.merge_branch(target_path, feature_branch, transport=transport)
                git_ops.push(target_path, branch=deploy_branch, transport=transport)
            except RuntimeError as e:
                print(f"  ❌ DELIVER failed: {e}")
                rec.outcome = Outcome.FAIL
                rec.phases.append(PhaseRecord(
                    phase=Phase.DELIVER, outcome=Outcome.FAIL,
                    detail=str(e)[:200],
                ))
                return False
            # Best-effort branch cleanup — don't abort on failure
            try:
                git_ops.delete_branch(target_path, feature_branch, transport=transport)
            except RuntimeError:
                print(f"  ⚠ Could not delete feature branch {feature_branch}")
            print(f"  Merged {feature_branch} into {deploy_branch} and pushed")
        else:
            print(f"  [DRY RUN] Would merge {feature_branch} into {deploy_branch}")

        archive_change(target_path, change_name, transport=transport)
        deliver_seconds = time.monotonic() - t0
        rec.phases.append(PhaseRecord(
            phase=Phase.DELIVER, outcome=Outcome.SUCCESS,
            seconds_used=deliver_seconds,
        ))

        total = time.monotonic() - cycle_start
        print(f"\n  {'='*50}")
        print(f"  ✅ DONE: {change_name}")
        print(f"  Total: {total:.1f}s | impl={impl_seconds:.1f}s verify={verify_seconds:.1f}s deliver={deliver_seconds:.1f}s")
        print(f"  {'='*50}")
        record_outcome(change_name, project_name, True, "deliver")
        return True

    # ── INTENT → task_type mapping for REFLECT ──────────────

    _INTENT_TO_TASK_TYPE = {
        IntentType.IMPLEMENTATION: "impl",
        IntentType.FIX: "fix",
    }

    @staticmethod
    def _get_last_rating(rec: ChangeRecord) -> str:
        """Extract the self_rating detail from the most recent reflect PhaseRecord."""
        for p in reversed(rec.phases):
            if p.phase == Phase.REFLECT:
                return p.detail or "computed"
        return "n/a"

    def phase_reflect(self, rec: ChangeRecord, change_name: str,
                      project_name: str, task_type: str,
                      change_dir: str, transport: Transport) -> float:
        """REFLECT phase: compute self-assessment metrics and write reflect.md.

        Returns elapsed time in seconds.
        """
        t0 = time.monotonic()

        # Compute metrics from phase records
        total_fix = sum(p.fix_attempts for p in rec.phases)
        actual_tokens = sum(p.prompt_tokens + p.completion_tokens for p in rec.phases)
        actual_steps = sum(p.llm_calls + p.tool_calls for p in rec.phases)
        outcome = "success" if rec.outcome == Outcome.SUCCESS else "reverted"

        # Self-rating algorithm
        if outcome == "reverted" or total_fix > 5:
            rating = "poor"
        elif total_fix == 0:
            rating = "excellent"
        elif total_fix <= 2:
            rating = "good"
        else:
            rating = "average"

        # Build strengths (rule-based)
        strengths = []
        impl_phase = next(
            (p for p in rec.phases if p.phase == Phase.IMPLEMENT), None
        )
        verify_phase = next(
            (p for p in rec.phases if p.phase == Phase.VERIFY), None
        )
        review_phase = next(
            (p for p in rec.phases if p.phase == Phase.REVIEW), None
        )

        if impl_phase and impl_phase.fix_attempts == 0:
            strengths.append("Clean implementation (no mechanical errors)")
        if verify_phase and verify_phase.fix_attempts == 0:
            strengths.append("First-pass verification")
        if impl_phase and impl_phase.fix_attempts == 0:
            strengths.append("Strong code generation accuracy")
        if review_phase and review_phase.outcome == Outcome.SUCCESS:
            strengths.append("Clean review (no critical issues)")

        # Build weaknesses (rule-based)
        weaknesses = []
        if impl_phase and impl_phase.fix_attempts > 0:
            weaknesses.append("Required mechanical error fixes")
        if verify_phase and verify_phase.fix_attempts > 0:
            weaknesses.append("Failed initial verification")
        if outcome == "reverted":
            weaknesses.append("Task exceeded recovery capacity")
        if review_phase and review_phase.outcome == Outcome.FAIL:
            weaknesses.append("Review found critical issues")

        # Build lessons
        lessons = []
        if rating == "excellent":
            lessons.append("First-pass success — maintain current approach")
        if impl_phase and impl_phase.fix_attempts > 0:
            lessons.append(
                f"Implementation required {impl_phase.fix_attempts} fix attempt(s)"
            )
        if verify_phase and verify_phase.fix_attempts > 0:
            lessons.append(
                f"Verification required {verify_phase.fix_attempts} fix attempt(s)"
            )
        if outcome == "reverted":
            lessons.append("Change reverted — review failure pattern")

        # Persist to DB
        record_self_assessment({
            "change_name": change_name,
            "task_type": task_type,
            "predicted_tokens": 0,
            "actual_tokens": actual_tokens,
            "predicted_steps": 0,
            "actual_steps": actual_steps,
            "fix_attempts": total_fix,
            "outcome": outcome,
            "self_rating": rating,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "lessons": lessons,
        })

        # Capability boundary detection (REQ-SA-04)
        recent = query_recent_ratings(task_type, limit=3)
        if len(recent) == 3 and all(r == "poor" for r in recent):
            record_lesson(
                title=f"Capability boundary: {task_type}",
                context=f"3 consecutive poor ratings for task_type={task_type}",
                takeaway=f"Recommend human intervention for {task_type} tasks",
                pattern_key=f"capability.boundary.{task_type}",
            )

        # Generate reflect.md
        reflect_lines = [
            f"# Self-Assessment: {change_name}",
            "",
            "## Task Review",
            "- predicted_tokens: 0",
            f"- actual_tokens: {actual_tokens}",
            "- predicted_steps: 0",
            f"- actual_steps: {actual_steps}",
            f"- fix_attempts: {total_fix}",
            "",
            "## Self-Rating",
            f"**{rating}**",
            "",
            "## Strengths",
        ]
        for s in strengths:
            reflect_lines.append(f"- {s}")
        reflect_lines.append("")
        reflect_lines.append("## Weaknesses")
        for w in weaknesses:
            reflect_lines.append(f"- {w}")
        reflect_lines.append("")
        reflect_lines.append("## Lessons Learned")
        for lesson in lessons:
            reflect_lines.append(f"- {lesson}")
        reflect_lines.append("")
        reflect_lines.append("## Next Time Suggestions")
        reflect_lines.append(
            f"- Estimated tokens for similar tasks: {actual_tokens}"
        )
        reflect_md = "\n".join(reflect_lines)

        # Write reflect.md to change_dir via transport
        reflect_path = f"{change_dir}/reflect.md"
        escaped = reflect_md.replace("'", "'\\''")
        transport.run_shell(
            f"echo '{escaped}' > '{reflect_path}'",
            timeout=10,
        )

        # Append PhaseRecord
        elapsed = time.monotonic() - t0
        rec.phases.append(
            PhaseRecord(phase=Phase.REFLECT, outcome=Outcome.SUCCESS,
                        seconds_used=elapsed, detail=rating)
        )
        return elapsed

    async def _fix_loop(self, target_path, project_config, errors,
                        pre_sha: str, transport: Transport,
                        max_attempts: int,
                        venv_python: str = None,
                        escalation: EscalationManager = None,
                        recovery: RecoveryManager = None) -> tuple[bool, int]:
        fix_turns = self.config.pipeline.fix_max_turns

        changed = _get_changed_files(target_path, pre_sha, transport)
        changed_info = f"\n本次变更的文件（只修这些）: {', '.join(changed) if changed else '无'}"
        path_hint = f"\n项目根目录: {target_path}"
        venv_hint = ""
        if venv_python:
            venv_hint = (
                f"\n\n## venv 配置（必须遵守）\n"
                f"项目使用 venv，所有命令 MUST 使用以下路径：\n"
                f"- Python: {venv_python}\n"
                f"- pip: {venv_python} -m pip\n"
                f"- pytest: {venv_python} -m pytest\n"
                f"不要使用 python、python3、pip、pip3 — 必须使用上方完整路径。"
            )

        for attempt in range(1, max_attempts + 1):
            print(f"    Fix attempt {attempt}/{max_attempts}...")

            # Build strategy hint from escalation or recovery (REQ-ES-03 / REQ-RI-05)
            strategy_hint = ""
            used_strategy = "same"
            if recovery:
                strategy = recovery.get_strategy()
                used_strategy = strategy.value
                strategy_hint = recovery.get_strategy_hint()
            elif escalation:
                strategy = escalation.next_strategy
                used_strategy = strategy.value
                if strategy == Strategy.DIFFERENT_APPROACH:
                    strategy_hint = (
                        "\n\n⚠️ 之前多次修复失败。"
                        "Try a fundamentally different approach. "
                        "Your previous strategy failed multiple times."
                    )
                elif strategy == Strategy.SIMPLIFY:
                    strategy_hint = (
                        "\n\n⚠️ Simplify the fix. "
                        "Remove complexity rather than adding more code."
                    )

            self.agent.set_phase(f"fix-{attempt}")
            register_tools(self.agent, target_path, transport=transport)

            if attempt == 1:
                await self.agent.run(
                    f"你是 zsiga 的修复引擎。项目根目录: {target_path}\n"
                    "严格遵守以下规则：\n"
                    "1. 只修改本次变更引入的文件（上方列出的）\n"
                    "2. 绝对不要修改任何未列出的文件\n"
                    "3. 不要添加新路由、新端点、新功能 — 只修复错误\n"
                    "4. 不要删除或替换 render_template、redirect 等现有调用\n"
                    "5. 只修报错的那一行，不要重排整个文件的 import 或做大规模重构\n"
                    "6. 所有 bash 命令必须先 cd 到项目根目录，不要猜测路径"
                    f"{venv_hint}{strategy_hint}",
                    f"错误:\n{errors}{changed_info}{path_hint}\n\n"
                    f"只修改上方列出的文件。修复后运行 {project_config.test_cmd} 确认。",
                    max_turns=fix_turns,
                )
            else:
                await self.agent.run(
                    f"你是 zsiga 的修复引擎。项目根目录: {target_path}\n"
                    "上一次修复没有解决问题。严格遵守以下规则：\n"
                    "1. 只修改本次变更引入的文件（上方列出的）\n"
                    "2. 绝对不要修改任何未列出的文件\n"
                    "3. 不要添加新路由、新端点、新功能\n"
                    "4. 只修报错的那一行，不要重排整个文件的 import 或做大规模重构\n"
                    "5. 如果无法在限制内修复，回复 STOP\n"
                    "6. 所有 bash 命令必须先 cd 到项目根目录，不要猜测路径"
                    f"{venv_hint}{strategy_hint}",
                    f"仍然存在的错误:\n{errors}{changed_info}{path_hint}\n\n"
                    f"只修改上方列出的文件。修复后运行 {project_config.test_cmd} 确认。",
                    max_turns=fix_turns,
                )

            passed, errors = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd,
                since_sha=pre_sha, transport=transport,
            )
            if passed:
                return True, attempt

            # Record failure to escalation or recovery (REQ-ES-02 / REQ-RI-05)
            if recovery:
                action = recovery.record_failure(errors, phase="implement")
                strategy_hint = action.strategy_hint
                if action.should_rollback:
                    print(f"  Recovery rollback after {attempt} fix attempts")
                    return False, attempt
            elif escalation:
                escalation.record_failure(
                    errors, phase="implement", strategy=used_strategy,
                )
                if escalation.should_abort():
                    print(f"  Escalation abort after {attempt} fix attempts")
                    return False, attempt

        return False, max_attempts

    async def _eval_fix_loop(self, change_dir, target_path, project_config,
                             pre_sha, transport: Transport,
                             max_attempts: int,
                             venv_python: str = None,
                             escalation: EscalationManager = None,
                             recovery: RecoveryManager = None) -> tuple[bool, int]:
        fix_turns = self.config.pipeline.fix_max_turns

        changed = _get_changed_files(target_path, pre_sha, transport)
        changed_info = f"\n本次变更的文件（只修这些）: {', '.join(changed) if changed else '无'}"
        path_hint = f"\n项目根目录: {target_path}"
        venv_hint = ""
        if venv_python:
            venv_hint = (
                f"\n\n## venv 配置（必须遵守）\n"
                f"项目使用 venv，所有命令 MUST 使用以下路径：\n"
                f"- Python: {venv_python}\n"
                f"- pip: {venv_python} -m pip\n"
                f"- pytest: {venv_python} -m pytest\n"
                f"不要使用 python、python3、pip、pip3 — 必须使用上方完整路径。"
            )

        for attempt in range(1, max_attempts + 1):
            print(f"    Eval fix attempt {attempt}/{max_attempts}...")

            # Build strategy hint from escalation or recovery (REQ-ES-03 / REQ-RI-05)
            strategy_hint = ""
            used_strategy = "same"
            if recovery:
                strategy = recovery.get_strategy()
                used_strategy = strategy.value
                strategy_hint = recovery.get_strategy_hint()
            elif escalation:
                strategy = escalation.next_strategy
                used_strategy = strategy.value
                if strategy == Strategy.DIFFERENT_APPROACH:
                    strategy_hint = (
                        "\n\n⚠️ 之前多次修复失败。"
                        "Try a fundamentally different approach. "
                        "Your previous strategy failed multiple times."
                    )
                elif strategy == Strategy.SIMPLIFY:
                    strategy_hint = (
                        "\n\n⚠️ Simplify the fix. "
                        "Remove complexity rather than adding more code."
                    )

            verify_file = f"{change_dir}/verify.md"
            r = transport.run_shell(f"cat '{verify_file}'", timeout=10)
            feedback = r["stdout"] if r["exit_code"] == 0 else "unknown"

            self.agent.set_phase(f"eval-fix-{attempt}")
            register_tools(self.agent, target_path, transport=transport)
            await self.agent.run(
                f"你是 zsiga 的修复引擎。项目根目录: {target_path}\n"
                "严格遵守以下规则：\n"
                "1. 只修改本次变更涉及的文件（上方列出的）\n"
                "2. 绝对不要修改任何未列出的文件\n"
                "3. 不要添加新路由、新端点、新功能 — 只修复验证反馈中的问题\n"
                "4. 不要删除或替换 render_template、redirect 等现有调用\n"
                "5. 只修报错的那一行，不要重排整个文件的 import 或做大规模重构\n"
                "6. 所有 bash 命令必须先 cd 到项目根目录，不要猜测路径"
                f"{venv_hint}{strategy_hint}",
                f"验证反馈:\n{feedback}{changed_info}{path_hint}\n\n"
                f"只修改上方列出的文件。修复后运行 {project_config.test_cmd} 确认。",
                max_turns=fix_turns,
            )

            passed, mech_errors = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd,
                since_sha=pre_sha, transport=transport,
            )
            if not passed:
                # Record failure to escalation or recovery (REQ-ES-05 / REQ-RI-05)
                if recovery:
                    action = recovery.record_failure(mech_errors, phase="verify")
                    if action.should_rollback:
                        print(f"  Recovery rollback after {attempt} eval-fix attempts")
                        return False, attempt
                elif escalation:
                    escalation.record_failure(
                        mech_errors, phase="verify", strategy=used_strategy,
                    )
                    if escalation.should_abort():
                        print(f"  Escalation abort after {attempt} eval-fix attempts")
                        return False, attempt
                return False, attempt

            self.agent.set_phase(f"re-verify-{attempt}")
            register_tools(self.agent, target_path, transport=transport)
            await verify(self.agent, change_dir, target_path, pre_sha,
                        transport=transport,
                        max_turns=self.config.pipeline.verify_max_turns,
                        timeout_seconds=self.config.pipeline.verify_timeout)
            new_verdict = read_verdict(change_dir, transport)
            if new_verdict == "PASS":
                return True, attempt

            # Re-verify still failed — record failure (REQ-ES-05 / REQ-RI-05)
            reverify_feedback = feedback
            r2 = transport.run_shell(f"cat '{verify_file}'", timeout=10)
            if r2["exit_code"] == 0:
                reverify_feedback = r2["stdout"]
            if recovery:
                action = recovery.record_failure(reverify_feedback, phase="verify")
                if action.should_rollback:
                    print(f"  Recovery rollback after {attempt} eval-fix attempts")
                    return False, attempt
            elif escalation:
                escalation.record_failure(
                    reverify_feedback, phase="verify", strategy=used_strategy,
                )
                if escalation.should_abort():
                    print(f"  Escalation abort after {attempt} eval-fix attempts")
                    return False, attempt

        return False, max_attempts

    def _handle_escalation_abort(self, escalation: EscalationManager,
                                  change_dir: str, change_name: str,
                                  project_name: str,
                                  transport: Transport,
                                  recovery: RecoveryManager = None) -> None:
        """Handle escalation abort: generate diagnosis, save, record lesson."""
        if recovery:
            recovery.generate_diagnostic_report()
            recovery.execute_rollback()
            return

        report = escalation.generate_diagnosis()
        report_text = report.to_text()

        # Save diagnosis report to change directory
        report_path = f"{change_dir}/escalation-diagnosis.md"
        escaped = report_text.replace("'", "'\\''")
        transport.run_shell(
            f"echo '{escaped}' > '{report_path}'",
            timeout=10,
        )
        print(f"  Escalation diagnosis saved to {report_path}")

        # Record lesson (REQ-ES-04)
        record_lesson(
            title=f"ESCALATION ABORT: {change_name}",
            context=f"project={project_name}, attempts={escalation.attempts}",
            takeaway=(
                f"Aborted after {escalation.attempts} failures. "
                f"{report.root_cause_hypothesis}"
            ),
            pattern_key="pipeline.fail.escalation",
            source="escalation",
        )

    def _run_diagnosis(self, change_dir: str, target_path: str,
                       change_name: str, project_name: str,
                       transport: Transport,
                       verify_feedback: str = "") -> None:
        """Run structured diagnosis and save report + record lesson."""
        print("  Running structured diagnosis...")
        diagnoser = Diagnoser()

        # Read verify.md feedback if not provided
        if not verify_feedback:
            verify_file = f"{change_dir}/verify.md"
            r = transport.run_shell(f"cat '{verify_file}'", timeout=10)
            verify_feedback = r["stdout"] if r["exit_code"] == 0 else ""

        # Read git diff for additional context
        diff_r = transport.run_shell(
            "git diff HEAD~1 --stat 2>/dev/null || echo ''",
            cwd=target_path, timeout=10,
        )
        diff_stat = diff_r.get("stdout", "")

        failure_info = {
            "detail": verify_feedback[:3000],
            "verify_feedback": verify_feedback[:3000],
            "change_name": change_name,
            "diff_stat": diff_stat[:500],
        }

        report = diagnoser.diagnose(failure_info, target_path, transport)
        report.save(change_dir, transport)
        print(f"  Diagnosis saved to {change_dir}/diagnosis.md")

        # Record lesson
        root_cause = report.fix_plan.root_cause
        record_lesson(
            title=f"DIAGNOSED: {change_name}",
            context=f"project={project_name}, root_cause={root_cause}",
            takeaway=f"Diagnosed root cause: {root_cause}. "
                     f"Fix: {report.fix_plan.fix_description}",
            pattern_key="pipeline.fail.verify.diagnosed",
            source="diagnoser",
        )

    def _ask_approval(self, change_name: str) -> bool:
        try:
            answer = input(f"  Approve '{change_name}'? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    def _try_create_issue(
        self, target_path: str, transport: Transport,
        change_name: str, proposal_text: str,
    ) -> int | None:
        """Attempt to create a GitHub Issue; returns number or None."""
        owner_repo = extract_github_repo(target_path, transport)
        if not owner_repo:
            print("  [github] Could not extract owner/repo, skipping Issue")
            return None
        token = self.config.github.token
        return create_issue(owner_repo, change_name, proposal_text, token)

    async def _dispatch_explore(self, prop, change_dir, target_path, transport) -> bool:
        """Dispatch explore-role sub-agent for research/investigation intents."""
        proposal_name = prop.get("proposal_filename", "proposal.md")
        proposal_text = read_file(f"{change_dir}/{proposal_name}", transport) or prop.get("id", "")
        agent = create_with_role(
            "explore",
            api_key=self.agent.client.api_key,
            model=self.agent.model,
            base_url=getattr(self.agent.client, "base_url", None),
        )
        result = await run_sub_agent(
            agent, target_path, transport, proposal_text,
            max_turns=15, timeout_seconds=300,
        )
        print(f"  Explore agent done: success={result.success}, {result.elapsed_seconds:.1f}s")
        print(f"  Result: {result.content[:200]}...")
        return result.success

    async def _dispatch_diagnoser(self, prop, change_dir, target_path, transport) -> bool:
        """Dispatch diagnoser for investigation intents."""
        proposal_name = prop.get("proposal_filename", "proposal.md")
        proposal_text = read_file(f"{change_dir}/{proposal_name}", transport) or prop.get("id", "")
        agent = create_with_role(
            "diagnoser",
            api_key=self.agent.client.api_key,
            model=self.agent.model,
            base_url=getattr(self.agent.client, "base_url", None),
        )
        result = await run_sub_agent(
            agent, target_path, transport, proposal_text,
            max_turns=15, timeout_seconds=300,
        )
        print(f"  Diagnoser agent done: success={result.success}, {result.elapsed_seconds:.1f}s")
        print(f"  Diagnosis: {result.content[:200]}...")
        return result.success

    async def _dispatch_review(self, prop, change_dir, target_path, transport) -> bool:
        """Dispatch review sub-agent for evaluation intents."""
        pre_sha = git_ops.rev_parse(target_path, transport=transport)
        await run_review(
            self.agent, change_dir, target_path, pre_sha, transport,
            max_turns=10, timeout_seconds=180,
        )
        verdict, issues = parse_review_verdict(change_dir, transport)
        print(f"  Review verdict: {verdict}")
        if issues:
            for issue in issues:
                print(f"    [{issue['severity']}] {issue['description'][:80]}")
        return verdict in ("CLEAN", "UNKNOWN")

    def close(self):
        for transport in self._transports.values():
            transport.close()
        self._transports.clear()


def _extract_calls(result) -> tuple[int, int]:
    if isinstance(result, RunResult):
        return (result.llm_calls, result.tool_calls)
    return (0, 0)


def _extract_tokens(result) -> tuple[int, int]:
    if isinstance(result, RunResult):
        return (result.prompt_tokens, result.completion_tokens)
    return (0, 0)


def _summarize_issues(issues: list[dict]) -> str:
    """Summarize review issues for PhaseRecord.detail (max 200 chars)."""
    if not issues:
        return ""
    parts = [f"[{i.get('severity', '?')}] {i.get('description', '')[:60]}" for i in issues]
    text = "; ".join(parts)
    return text[:200]
