import asyncio
import time
from datetime import datetime

from ..agent.loop import AgentLoop, RunResult
from ..agent.tools import register_tools
from ..config import ZsigaConfig
from ..intake.scanner import DirectoryScanner
from .. import git_ops
from ..memory.context import load_active_context, update_active_context, load_recent_lessons
from ..memory.learn import record_outcome
from ..metrics.types import ChangeRecord, PhaseRecord, Phase, Outcome
from ..metrics.collector import record_change
from ..transport import Transport, LocalTransport, create_transport
from .enricher import enrich
from .implementer import implement
from .verifier import verify, read_verdict
from .utils import verify_mechanical, archive_change, _get_changed_files, read_file
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

            if await self._process_change(prop):
                processed += 1

        self._update_memory()

        print(f"\n{'='*60}")
        print(f"Cycle complete: {processed} changes processed")
        print(f"{'='*60}")

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

        rec = ChangeRecord(
            change_name=change_name,
            project=project_name,
            outcome=Outcome.SUCCESS,
            started_at=datetime.now().isoformat(),
        )

        try:
            return await self._run_phases(prop, rec, change_dir, target_path,
                                          project_name, project_config, change_name,
                                          transport)
        finally:
            record_change(rec)

    async def _run_phases(self, prop, rec, change_dir, target_path,
                          project_name, project_config, change_name,
                          transport: Transport) -> bool:
        cycle_start = time.monotonic()

        # Prefetch project context once (shared by enrich + implement)
        print(f"  Prefetching project context...")
        t_pf = time.monotonic()
        proposal_text = read_file(f"{change_dir}/proposal.md", transport) or ""
        project_context = build_project_context(target_path, transport,
                                                 proposal=proposal_text)
        print(f"  Project context ready ({len(project_context)} chars, {time.monotonic() - t_pf:.1f}s)")

        # Phase 1: ENRICH
        if not (prop["has_specs"] and prop["has_design"] and prop["has_tasks"]):
            print(f"\n  {'='*50}")
            print(f"  Phase 1/4: ENRICH {change_name}")
            print(f"  {'='*50}")
            self.agent.set_phase("enrich")
            register_tools(self.agent, target_path, transport=transport)
            t0 = time.monotonic()
            enrich_result = await enrich(self.agent, change_dir, target_path,
                        transport=transport,
                        project_context=project_context,
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

        # Approval gate
        if self.config.safety.require_approval:
            approved = self._ask_approval(change_name)
            if not approved:
                print(f"  Skipped: not approved")
                rec.outcome = Outcome.SKIPPED
                return False

        # Phase 2: IMPLEMENT
        print(f"\n  {'='*50}")
        print(f"  Phase 2/4: IMPLEMENT {change_name}")
        print(f"  {'='*50}")
        self.agent.set_phase("impl")
        pre_sha = git_ops.rev_parse(target_path, transport=transport)
        print(f"  Pre-impl SHA: {pre_sha}")
        register_tools(self.agent, target_path, transport=transport)
        t0 = time.monotonic()
        impl_result = await implement(self.agent, change_dir, target_path,
                       transport=transport,
                       project_context=project_context,
                       max_turns=self.config.pipeline.impl_max_turns,
                        timeout_seconds=self.config.pipeline.impl_timeout)
        impl_seconds = time.monotonic() - t0
        impl_calls = _extract_calls(impl_result)
        impl_tokens = _extract_tokens(impl_result)
        print(f"  Phase 2 done in {impl_seconds:.1f}s")

        # Mechanical verification (only check changed files)
        print(f"\n  Mechanical verification...")
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
            print(f"  Attempting fixes...")
            fixed, fix_attempts = await self._fix_loop(
                target_path, project_config,
                errors, pre_sha=pre_sha, transport=transport,
                max_attempts=self.config.pipeline.fix_attempts,
            )
            if not fixed:
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

        # Phase 3: VERIFY
        print(f"\n  {'='*50}")
        print(f"  Phase 3/4: VERIFY {change_name}")
        print(f"  {'='*50}")
        self.agent.set_phase("verify")
        register_tools(self.agent, target_path, transport=transport)

        print(f"  Prefetching test/lint results...")
        t_mech = time.monotonic()
        mech_results = prefetch_mechanical(
            target_path, project_config.test_cmd, project_config.lint_cmd,
            since_sha=pre_sha,
            transport=transport,
        )
        print(f"  Test: {'✅' if mech_results['test']['passed'] else '❌'}, "
              f"Lint: {'✅' if mech_results['lint']['passed'] else '❌'} "
              f"({time.monotonic() - t_mech:.1f}s)")

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
            print(f"  Verifier: FAIL, attempting eval fixes...")
            fixed, eval_fix_attempts = await self._eval_fix_loop(
                change_dir, target_path, project_config,
                pre_sha, transport=transport,
                max_attempts=self.config.pipeline.eval_fix_attempts,
            )
            if not fixed:
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

        # Phase 4: DELIVER
        print(f"\n  {'='*50}")
        print(f"  Phase 4/4: DELIVER {change_name}")
        print(f"  {'='*50}")
        t0 = time.monotonic()
        if git_ops.has_uncommitted_changes(target_path, transport=transport):
            git_ops.add_all(target_path, transport=transport)
            git_ops.commit(target_path, f"feat({project_name}): {change_name}",
                          transport=transport)
        git_ops.tag(target_path, f"zsiga-{change_name}", transport=transport)
        git_ops.push(target_path, dry_run=self.config.safety.dry_run,
                    transport=transport)

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

    async def _fix_loop(self, target_path, project_config, errors,
                        pre_sha: str, transport: Transport,
                        max_attempts: int) -> tuple[bool, int]:
        fix_turns = self.config.pipeline.fix_max_turns

        changed = _get_changed_files(target_path, pre_sha, transport)
        changed_info = f"\n本次变更的文件（只修这些）: {', '.join(changed) if changed else '无'}"

        for attempt in range(1, max_attempts + 1):
            print(f"    Fix attempt {attempt}/{max_attempts}...")
            self.agent.set_phase(f"fix-{attempt}")
            register_tools(self.agent, target_path, transport=transport)

            if attempt == 1:
                await self.agent.run(
                    "你是 zsiga 的修复引擎。严格遵守以下规则：\n"
                    "1. 只修改本次变更引入的文件（上方列出的）\n"
                    "2. 绝对不要修改任何未列出的文件\n"
                    "3. 不要添加新路由、新端点、新功能 — 只修复错误\n"
                    "4. 不要删除或替换 render_template、redirect 等现有调用",
                    f"错误:\n{errors}{changed_info}\n\n"
                    f"只修改上方列出的文件。修复后运行 {project_config.test_cmd} 确认。",
                    max_turns=fix_turns,
                )
            else:
                await self.agent.run(
                    "你是 zsiga 的修复引擎。上一次修复没有解决问题。严格遵守以下规则：\n"
                    "1. 只修改本次变更引入的文件（上方列出的）\n"
                    "2. 绝对不要修改任何未列出的文件\n"
                    "3. 不要添加新路由、新端点、新功能\n"
                    "4. 如果无法在限制内修复，回复 STOP",
                    f"仍然存在的错误:\n{errors}{changed_info}\n\n"
                    f"只修改上方列出的文件。修复后运行 {project_config.test_cmd} 确认。",
                    max_turns=fix_turns,
                )

            passed, errors = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd,
                since_sha=pre_sha, transport=transport,
            )
            if passed:
                return True, attempt
        return False, max_attempts

    async def _eval_fix_loop(self, change_dir, target_path, project_config,
                             pre_sha, transport: Transport,
                             max_attempts: int) -> tuple[bool, int]:
        fix_turns = self.config.pipeline.fix_max_turns

        changed = _get_changed_files(target_path, pre_sha, transport)
        changed_info = f"\n本次变更的文件（只修这些）: {', '.join(changed) if changed else '无'}"

        for attempt in range(1, max_attempts + 1):
            print(f"    Eval fix attempt {attempt}/{max_attempts}...")
            verify_file = f"{change_dir}/verify.md"
            r = transport.run_shell(f"cat '{verify_file}'", timeout=10)
            feedback = r["stdout"] if r["exit_code"] == 0 else "unknown"

            self.agent.set_phase(f"eval-fix-{attempt}")
            register_tools(self.agent, target_path, transport=transport)
            await self.agent.run(
                "你是 zsiga 的修复引擎。严格遵守以下规则：\n"
                "1. 只修改本次变更涉及的文件（上方列出的）\n"
                "2. 绝对不要修改任何未列出的文件\n"
                "3. 不要添加新路由、新端点、新功能 — 只修复验证反馈中的问题\n"
                "4. 不要删除或替换 render_template、redirect 等现有调用",
                f"验证反馈:\n{feedback}{changed_info}\n\n"
                f"只修改上方列出的文件。修复后运行 {project_config.test_cmd} 确认。",
                max_turns=fix_turns,
            )

            passed, _ = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd,
                since_sha=pre_sha, transport=transport,
            )
            if not passed:
                return False, attempt

            self.agent.set_phase(f"re-verify-{attempt}")
            register_tools(self.agent, target_path, transport=transport)
            await verify(self.agent, change_dir, target_path, pre_sha,
                        transport=transport,
                        max_turns=self.config.pipeline.verify_max_turns,
                        timeout_seconds=self.config.pipeline.verify_timeout)
            if read_verdict(change_dir, transport) == "PASS":
                return True, attempt
        return False, max_attempts

    def _ask_approval(self, change_name: str) -> bool:
        try:
            answer = input(f"  Approve '{change_name}'? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

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
