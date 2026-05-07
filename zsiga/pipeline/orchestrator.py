import asyncio
import time
from datetime import datetime
from pathlib import Path

from ..agent.loop import AgentLoop
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
from .utils import verify_mechanical, archive_change


class ZsigaOrchestrator:

    def __init__(self, config: ZsigaConfig):
        self.config = config
        self.agent = AgentLoop(
            config.llm.api_key,
            config.llm.model,
            base_url=config.llm.base_url,
            proxy=config.llm.proxy,
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
        # Phase 1: ENRICH
        if not (prop["has_specs"] and prop["has_design"] and prop["has_tasks"]):
            print(f"  Phase 1: Enriching {change_name}...")
            register_tools(self.agent, target_path, transport=transport)
            t0 = time.monotonic()
            await enrich(self.agent, change_dir, target_path,
                        max_turns=self.config.pipeline.enrich_max_turns,
                        timeout_seconds=self.config.pipeline.enrich_timeout)
            rec.phases.append(PhaseRecord(
                phase=Phase.ENRICH, outcome=Outcome.SUCCESS,
                seconds_used=time.monotonic() - t0,
            ))
            print(f"  Enriched.")

        # Approval gate
        if self.config.safety.require_approval:
            approved = self._ask_approval(change_name)
            if not approved:
                print(f"  Skipped: not approved")
                rec.outcome = Outcome.SKIPPED
                return False

        # Phase 2: IMPLEMENT
        print(f"  Phase 2: Implementing {change_name}...")
        pre_sha = git_ops.rev_parse(target_path, transport=transport)
        register_tools(self.agent, target_path, transport=transport)
        t0 = time.monotonic()
        await implement(self.agent, change_dir, target_path,
                       max_turns=self.config.pipeline.impl_max_turns,
                       timeout_seconds=self.config.pipeline.impl_timeout)
        impl_seconds = time.monotonic() - t0

        # Mechanical verification (only check changed files)
        fix_attempts = 0
        passed, errors = verify_mechanical(
            target_path, project_config.test_cmd, project_config.lint_cmd,
            since_sha=pre_sha, transport=transport,
        )
        if not passed:
            print(f"  Mechanical verification FAILED, attempting fixes...")
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
                ))
                record_outcome(change_name, project_name, False, "implement", errors)
                return False

        rec.phases.append(PhaseRecord(
            phase=Phase.IMPLEMENT, outcome=Outcome.SUCCESS,
            seconds_used=impl_seconds, fix_attempts=fix_attempts,
        ))

        # Phase 3: VERIFY
        print(f"  Phase 3: Verifying {change_name}...")
        register_tools(self.agent, target_path, transport=transport)
        t0 = time.monotonic()
        await verify(self.agent, change_dir, target_path, pre_sha,
                    max_turns=self.config.pipeline.verify_max_turns,
                    timeout_seconds=self.config.pipeline.verify_timeout)
        verify_seconds = time.monotonic() - t0

        verdict = read_verdict(change_dir)
        verify_outcome = Outcome.SUCCESS if verdict == "PASS" else Outcome.FAIL
        eval_fix_attempts = 0

        if verdict == "FAIL":
            print(f"  Verifier: FAIL, attempting fixes...")
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
                ))
                record_outcome(change_name, project_name, False, "verify")
                return False

        rec.phases.append(PhaseRecord(
            phase=Phase.VERIFY, outcome=verify_outcome,
            seconds_used=verify_seconds, fix_attempts=eval_fix_attempts,
        ))

        # Phase 4: DELIVER
        print(f"  Phase 4: Delivering {change_name}...")
        t0 = time.monotonic()
        if git_ops.has_uncommitted_changes(target_path, transport=transport):
            git_ops.add_all(target_path, transport=transport)
            git_ops.commit(target_path, f"feat({project_name}): {change_name}",
                          transport=transport)
        git_ops.tag(target_path, f"zsiga-{change_name}", transport=transport)
        git_ops.push(target_path, dry_run=self.config.safety.dry_run,
                    transport=transport)

        archive_change(target_path, change_name, transport=transport)
        rec.phases.append(PhaseRecord(
            phase=Phase.DELIVER, outcome=Outcome.SUCCESS,
            seconds_used=time.monotonic() - t0,
        ))
        print(f"  ✓ Done: {change_name}")
        record_outcome(change_name, project_name, True, "deliver")
        return True

    async def _fix_loop(self, target_path, project_config, errors,
                        pre_sha: str, transport: Transport,
                        max_attempts: int) -> tuple[bool, int]:
        fix_turns = self.config.pipeline.fix_max_turns
        for attempt in range(1, max_attempts + 1):
            print(f"    Fix attempt {attempt}/{max_attempts}...")
            register_tools(self.agent, target_path, transport=transport)
            await self.agent.run(
                "你是 zsiga 的修复引擎。修复以下错误。不要添加新功能。",
                f"错误:\n{errors}\n\n修复后运行 {project_config.test_cmd} 和 {project_config.lint_cmd}",
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
        for attempt in range(1, max_attempts + 1):
            print(f"    Eval fix attempt {attempt}/{max_attempts}...")
            verify_file = f"{change_dir}/verify.md"
            r = transport.run_shell(f"cat '{verify_file}'", timeout=10)
            feedback = r["stdout"] if r["exit_code"] == 0 else "unknown"

            register_tools(self.agent, target_path, transport=transport)
            await self.agent.run(
                "你是 zsiga 的修复引擎。修复验证发现的问题。不要添加新功能。",
                f"验证反馈:\n{feedback}\n\n修复后运行 {project_config.test_cmd}",
                max_turns=fix_turns,
            )

            passed, _ = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd,
                since_sha=pre_sha, transport=transport,
            )
            if not passed:
                return False, attempt

            register_tools(self.agent, target_path, transport=transport)
            await verify(self.agent, change_dir, target_path, pre_sha,
                        max_turns=self.config.pipeline.verify_max_turns,
                        timeout_seconds=self.config.pipeline.verify_timeout)
            if read_verdict(change_dir) == "PASS":
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
