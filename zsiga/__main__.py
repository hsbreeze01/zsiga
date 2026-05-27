import asyncio
import re
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler  # noqa: E402

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from .config import load_config  # noqa: E402
from .pipeline.orchestrator import ZsigaOrchestrator  # noqa: E402
from .metrics.dashboard import generate_dashboard  # noqa: E402
from .metrics.collector import load_all_changes  # noqa: E402
from .transport import create_transport  # noqa: E402
from .daemon import daemon_loop  # noqa: E402
from .agent.permissions import ensure_permissions  # noqa: E402


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^a-z0-9\u4e00-\u9fff-]', '', text, flags=re.UNICODE)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60] or 'unnamed-change'


def cmd_propose(args: list[str]):
    project_name = None
    description = None
    change_name_override = None
    plan_only = "--plan-only" in args
    run_pipeline = "--run" in args

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--name" and i + 1 < len(args):
            change_name_override = args[i + 1]
            i += 2
        elif a == "--description" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif a in ("--plan-only", "--run"):
            i += 1
        elif project_name is None:
            project_name = a
            i += 1
        elif description is None:
            description = a
            i += 1
        else:
            i += 1

    if not project_name or not description:
        print("Usage: python3.11 -m zsiga propose <project> --description <desc>")
        print("                                [--name <change-name>] [--run] [--plan-only]")
        print("  or:  python3.11 -m zsiga propose <project> <description>")
        print(f"\nProjects: {', '.join(load_config().targets.keys())}")
        sys.exit(1)

    config = load_config()
    if project_name not in config.targets:
        print(f"Unknown project: {project_name}")
        print(f"Available: {', '.join(config.targets.keys())}")
        sys.exit(1)

    target = config.targets[project_name]
    transport = create_transport(target)
    if change_name_override:
        change_name = _slugify(change_name_override)
    else:
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

    if plan_only or not run_pipeline:
        if plan_only:
            print("\n  --plan-only: stopping before pipeline")
        else:
            print("\n  Tip: add --run to start the pipeline")
        return

    print("\n  Starting pipeline...")
    asyncio.run(_run_single(config, project_name, change_name, change_dir, target.path))


async def _run_single(config, project_name, change_name, change_dir, target_path):
    orchestrator = ZsigaOrchestrator(config)
    try:
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
    ensure_permissions(reauth="--reauth" in sys.argv[2:])
    orchestrator = ZsigaOrchestrator(config)
    try:
        asyncio.run(orchestrator.run_cycle())
    finally:
        orchestrator.close()


def cmd_projects():
    config = load_config()
    print(f"{'Project':<15} {'Transport':<10} {'Target':<50} {'Status'}")
    print(f"{'-'*15} {'-'*10} {'-'*50} {'-'*10}")
    for name, tc in config.targets.items():
        transport = create_transport(tc)
        r = transport.run_shell("echo OK", timeout=5)
        status = "✅ connected" if r["exit_code"] == 0 else "❌ failed"
        transport_type = tc.transport or "local"
        target_display = tc.path if len(tc.path) <= 48 else "..." + tc.path[-45:]
        print(f"{name:<15} {transport_type:<10} {target_display:<50} {status}")
        if tc.transport == "ssh" and tc.ssh:
            print(f"{'':<15} {'':<10} ssh://{tc.ssh.user}@{tc.ssh.host}:{tc.ssh.port}")


def cmd_status():
    config = load_config()
    changes = load_all_changes()

    for name, tc in config.targets.items():
        transport = create_transport(tc)
        changes_dir = f"{tc.path}/openspec/changes"
        r = transport.run_shell(f"ls -1 '{changes_dir}' 2>/dev/null", timeout=5)
        pending = [d for d in r.get("stdout", "").strip().split("\n") if d and d != "archive"]
        archive_r = transport.run_shell(f"ls -1 '{changes_dir}/archive' 2>/dev/null", timeout=5)
        archived = [d for d in archive_r.get("stdout", "").strip().split("\n") if d]

        print(f"\n📦 {name} ({tc.transport})")
        if pending:
            for p in pending:
                print(f"  ⏳ {p}")
        else:
            print("  (no pending changes)")
        if archived:
            print(f"  📁 archive: {len(archived)} completed")

    if changes:
        print(f"\n{'='*60}")
        print("Recent outcomes:")
        recent = changes[-10:]
        for c in reversed(recent):
            icon = {"success": "✅", "reverted": "❌", "fail": "❌", "skipped": "⏭️"}.get(c.get("outcome", ""), "❓")
            duration = ""
            if c.get("started_at") and c.get("finished_at"):
                try:
                    from datetime import datetime
                    s = datetime.fromisoformat(c["started_at"])
                    e = datetime.fromisoformat(c["finished_at"])
                    duration = f" ({(e-s).total_seconds():.0f}s)"
                except Exception:
                    pass
            print(f"  {icon} {c['change_name']:<40} {c['project']:<12} {c.get('outcome', '?')}{duration}")


def cmd_log(args: list[str]):
    changes = load_all_changes()
    if not changes:
        print("No change history yet.")
        return

    limit = 20
    for a in args:
        if a.startswith("--limit="):
            limit = int(a.split("=")[1])
        elif a.startswith("-n"):
            limit = int(a[2:])

    project_filter = None
    for a in args:
        if not a.startswith("-"):
            project_filter = a
            break

    filtered = changes
    if project_filter:
        filtered = [c for c in changes if c.get("project") == project_filter]

    print(f"{'Change':<40} {'Project':<12} {'Outcome':<10} {'Duration':<10} {'Started'}")
    print(f"{'-'*40} {'-'*12} {'-'*10} {'-'*10} {'-'*20}")

    for c in reversed(filtered[-limit:]):
        outcome = c.get("outcome", "?")
        icon = {"success": "✅", "reverted": "❌", "fail": "❌"}.get(outcome, "❓")
        duration = ""
        if c.get("started_at") and c.get("finished_at"):
            try:
                from datetime import datetime
                s = datetime.fromisoformat(c["started_at"])
                e = datetime.fromisoformat(c["finished_at"])
                duration = f"{(e-s).total_seconds():.0f}s"
            except Exception:
                pass
        started = c.get("started_at", "")[:19].replace("T", " ")
        print(f"{icon} {c['change_name']:<38} {c.get('project', '?'):<12} {outcome:<10} {duration:<10} {started}")

        for p in c.get("phases", []):
            psec = f"{p.get('seconds_used', 0):.0f}s" if p.get("seconds_used") else ""
            fix = f" fixes={p['fix_attempts']}" if p.get("fix_attempts") else ""
            print(f"    {p['phase']:<12} {p['outcome']:<10} {psec}{fix}")


def cmd_dashboard(args: list[str]):
    serve = "--serve" in args
    port = 58175
    for a in args:
        if a.startswith("--port="):
            port = int(a.split("=")[1])

    path = generate_dashboard()
    print(f"Dashboard generated: {path}")

    if serve:
        import os
        serve_dir = os.path.dirname(path)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=serve_dir, **kwargs)

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("0.0.0.0", port), Handler)
        print(f"Serving at http://localhost:{port}")
        print("Press Ctrl+C to stop")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def cmd_daemon(args: list[str]):
    dashboard_port = 58175
    reauth = False
    for a in args:
        if a.startswith("--port="):
            dashboard_port = int(a.split("=")[1])
        elif a == "--no-dashboard":
            dashboard_port = None
        elif a == "--reauth":
            reauth = True

    config = load_config()
    ensure_permissions(reauth=reauth)
    daemon_loop(config, dashboard_port=dashboard_port)


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
    elif subcmd == "projects":
        cmd_projects()
    elif subcmd == "status":
        cmd_status()
    elif subcmd == "log":
        cmd_log(rest)
    elif subcmd == "dashboard":
        cmd_dashboard(rest)
    elif subcmd == "daemon":
        cmd_daemon(rest)
    else:
        print(f"Unknown command: {subcmd}")
        print("Usage:")
        print("  python3.11 -m zsiga propose <project> <desc>       # create + run")
        print("  python3.11 -m zsiga propose <project> <desc> --plan-only")
        print("  python3.11 -m zsiga run                            # scan + run pending")
        print("  python3.11 -m zsiga projects                       # list projects + status")
        print("  python3.11 -m zsiga status                         # pending changes + history")
        print("  python3.11 -m zsiga log [project] [-n20]           # change history")
        print("  python3.11 -m zsiga dashboard [--serve] [--port=N] # metrics dashboard")
        print("  python3 -m zsiga daemon [--port=N] [--no-dashboard]  # run as daemon")
        sys.exit(1)


if __name__ == "__main__":
    main()
