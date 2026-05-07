import asyncio
import re
import sys
from .config import load_config
from .pipeline.orchestrator import ZsigaOrchestrator
from .metrics.dashboard import generate_dashboard
from .transport import LocalTransport, create_transport


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^a-z0-9\u4e00-\u9fff-]', '', text, flags=re.UNICODE)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60] or 'unnamed-change'


def cmd_propose(args: list[str]):
    if len(args) < 2:
        print("Usage: python3.11 -m zsiga propose <project> <description>")
        print("       python3.11 -m zsiga propose <project> <description> --plan-only")
        print(f"\nProjects: {', '.join(load_config().targets.keys())}")
        sys.exit(1)

    project_name = args[0]
    description = args[1]
    plan_only = "--plan-only" in args

    config = load_config()
    if project_name not in config.targets:
        print(f"Unknown project: {project_name}")
        print(f"Available: {', '.join(config.targets.keys())}")
        sys.exit(1)

    target = config.targets[project_name]
    transport = create_transport(target)
    change_name = _slugify(description)
    if not change_name:
        change_name = "unnamed-change"

    change_dir = f"{target.path}/openspec/changes/{change_name}"

    r = transport.run_shell(f"test -d '{change_dir}' && echo EXISTS", timeout=5)
    if "EXISTS" in r.get("stdout", ""):
        print(f"Change already exists: {change_name}")
        print(f"  Path: {change_dir}")
        sys.exit(1)

    transport.run_shell(f"mkdir -p '{change_dir}'", timeout=5)

    proposal_content = (
        f"# Proposal: {description}\n\n"
        f"## Summary\n{description}\n\n"
        f"## Motivation\n\n"
        f"## Expected Behavior\n\n"
    )

    r = transport.run_shell(
        f"cat > '{change_dir}/proposal.md'",
        stdin_data=proposal_content,
        timeout=10,
    )
    if r["exit_code"] != 0:
        print(f"Failed to create proposal: {r['stderr']}")
        sys.exit(1)

    print(f"✓ Proposed: {change_name}")
    print(f"  Project: {project_name}")
    print(f"  Path:    {change_dir}")

    if plan_only:
        print(f"\n  --plan-only: stopping before pipeline")
        return

    print(f"\n  Starting pipeline...")
    asyncio.run(_run_single(config, project_name, change_name, change_dir, target.path))


async def _run_single(config, project_name, change_name, change_dir, target_path):
    orchestrator = ZsigaOrchestrator(config)
    try:
        transport = create_transport(config.targets[project_name])

        prop = {
            "id": change_name,
            "project": project_name,
            "target_path": target_path,
            "change_dir": change_dir,
            "has_proposal": True,
            "has_specs": False,
            "has_design": False,
            "has_tasks": False,
        }
        await orchestrator._process_change(prop)
    finally:
        orchestrator.close()


def cmd_run():
    config = load_config()
    orchestrator = ZsigaOrchestrator(config)
    try:
        asyncio.run(orchestrator.run_cycle())
    finally:
        orchestrator.close()


def main():
    if len(sys.argv) < 2:
        cmd_run()
        return

    subcmd = sys.argv[1]
    rest = sys.argv[2:]

    if subcmd == "propose":
        cmd_propose(rest)
    elif subcmd == "run":
        cmd_run()
    elif subcmd == "dashboard":
        path = generate_dashboard()
        print(f"Dashboard generated: {path}")
    else:
        print(f"Unknown command: {subcmd}")
        print("Usage:")
        print("  python3.11 -m zsiga                          # run pipeline")
        print("  python3.11 -m zsiga run                      # run pipeline")
        print("  python3.11 -m zsiga propose <project> <desc> # create + run")
        print("  python3.11 -m zsiga propose <project> <desc> --plan-only")
        print("  python3.11 -m zsiga dashboard                # generate dashboard")
        sys.exit(1)


if __name__ == "__main__":
    main()
