import asyncio
from pathlib import Path

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from ..config import ZsigaConfig
from ..intake.scanner import DirectoryScanner
from .. import git_ops
from .enricher import enrich
from .implementer import implement
from .verifier import verify, read_verdict
from .utils import verify_mechanical, archive_change


class ZsigaOrchestrator:

    def __init__(self, config: ZsigaConfig):
        self.config = config
        self.agent = AgentLoop(config.llm.api_key, config.llm.model)

    async def run_cycle(self):
        scanner = DirectoryScanner(self.config.targets)
        proposals = scanner.scan()

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

        print(f"\n{'='*60}")
        print(f"Cycle complete: {processed} changes processed")
        print(f"{'='*60}")

    async def _process_change(self, prop: dict) -> bool:
        change_dir = prop["change_dir"]
        target_path = prop["target_path"]
        project_name = prop["project"]
        project_config = self.config.targets[project_name]
        change_name = prop["id"]

        # Phase 1: ENRICH
        if not (prop["has_specs"] and prop["has_design"] and prop["has_tasks"]):
            print(f"  Phase 1: Enriching {change_name}...")
            register_tools(self.agent, target_path)
            await enrich(self.agent, change_dir, target_path)
            print(f"  Enriched.")

        # Approval gate
        if self.config.safety.require_approval:
            approved = self._ask_approval(change_name)
            if not approved:
                print(f"  Skipped: not approved")
                return False

        # Phase 2: IMPLEMENT
        print(f"  Phase 2: Implementing {change_name}...")
        pre_sha = git_ops.rev_parse(target_path)
        register_tools(self.agent, target_path)
        await implement(self.agent, change_dir, target_path)

        # Mechanical verification
        passed, errors = verify_mechanical(
            target_path, project_config.test_cmd, project_config.lint_cmd
        )
        if not passed:
            print(f"  Mechanical verification FAILED, attempting fixes...")
            fixed = await self._fix_loop(
                target_path, project_config,
                errors, max_attempts=self.config.pipeline.fix_attempts,
            )
            if not fixed:
                git_ops.reset_hard(target_path, pre_sha)
                print(f"  REVERTED: {change_name}")
                return False

        # Phase 3: VERIFY
        print(f"  Phase 3: Verifying {change_name}...")
        register_tools(self.agent, target_path)
        await verify(self.agent, change_dir, target_path, pre_sha)

        verdict = read_verdict(change_dir)
        if verdict == "FAIL":
            print(f"  Verifier: FAIL, attempting fixes...")
            fixed = await self._eval_fix_loop(
                change_dir, target_path, project_config,
                pre_sha, max_attempts=self.config.pipeline.eval_fix_attempts,
            )
            if not fixed:
                git_ops.reset_hard(target_path, pre_sha)
                print(f"  REVERTED: {change_name} (verify failed)")
                return False

        # Phase 4: DELIVER
        print(f"  Phase 4: Delivering {change_name}...")
        if git_ops.has_uncommitted_changes(target_path):
            git_ops.add_all(target_path)
            git_ops.commit(target_path, f"feat({project_name}): {change_name}")
        git_ops.tag(target_path, f"zsiga-{change_name}")
        git_ops.push(target_path)

        archive_change(target_path, change_name)
        print(f"  ✓ Done: {change_name}")
        return True

    async def _fix_loop(self, target_path, project_config, errors,
                        max_attempts: int) -> bool:
        for attempt in range(1, max_attempts + 1):
            print(f"    Fix attempt {attempt}/{max_attempts}...")
            register_tools(self.agent, target_path)
            await self.agent.run(
                "你是 zsiga 的修复引擎。修复以下错误。不要添加新功能。",
                f"错误:\n{errors}\n\n修复后运行 {project_config.test_cmd} 和 {project_config.lint_cmd}",
            )
            passed, errors = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd
            )
            if passed:
                return True
        return False

    async def _eval_fix_loop(self, change_dir, target_path, project_config,
                             pre_sha, max_attempts: int) -> bool:
        for attempt in range(1, max_attempts + 1):
            print(f"    Eval fix attempt {attempt}/{max_attempts}...")
            verify_file = Path(change_dir) / "verify.md"
            feedback = verify_file.read_text() if verify_file.exists() else "unknown"

            register_tools(self.agent, target_path)
            await self.agent.run(
                "你是 zsiga 的修复引擎。修复验证发现的问题。不要添加新功能。",
                f"验证反馈:\n{feedback}\n\n修复后运行 {project_config.test_cmd}",
            )

            passed, _ = verify_mechanical(
                target_path, project_config.test_cmd, project_config.lint_cmd
            )
            if not passed:
                return False

            register_tools(self.agent, target_path)
            await verify(self.agent, change_dir, target_path, pre_sha)
            if read_verdict(change_dir) == "PASS":
                return True
        return False

    def _ask_approval(self, change_name: str) -> bool:
        try:
            answer = input(f"  Approve '{change_name}'? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False
