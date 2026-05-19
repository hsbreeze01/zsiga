"""
zsiga daemon — runs pipeline cycles in a loop.

Features:
- PID lock file for mutual exclusion (<repo>/data/lock.pid)
- SIGUSR1 to pause (finish current cycle, then wait)
- SIGUSR2 to resume
- SIGTERM/SIGINT to graceful shutdown (finish current cycle, then exit)
- Optional dashboard HTTP server forked at startup
- Cycle interval from config: pipeline.cycle_interval_hours (default 8)
"""

import json
import os
import signal
import sys
import time
import asyncio
import fcntl
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread


class DaemonState:
    """Shared mutable state for signal handlers."""
    paused = False
    shutdown = False


def _lock_path() -> Path:
    """Return PID lock file path. Use ZSIGA_HOME or repo root."""
    home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
    data_dir = Path(home) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "lock.pid"


def _daemon_state_path() -> Path:
    """Return daemon state file path."""
    home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
    return Path(home) / "data" / "daemon_state.json"


def _write_daemon_state(
    started_at: str,
    cycle: int,
    state: str = "running",
    current_change: str | None = None,
    current_phase: str | None = None,
    current_project: str | None = None,
):
    """Write daemon_state.json with current daemon status."""
    data = {
        "pid": os.getpid(),
        "started_at": started_at,
        "cycle": cycle,
        "state": state,
        "current_change": current_change,
        "current_phase": current_phase,
        "current_project": current_project,
        "last_heartbeat": datetime.now().isoformat(),
    }
    path = _daemon_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def acquire_lock():
    """Try to acquire PID lock. Returns (fd, True) on success, (None, False) on failure."""
    lock_file = _lock_path()
    fd = open(lock_file, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        existing_pid = fd.read().strip()
        print(f"❌ Another zsiga daemon is running (PID {existing_pid})")
        print(f"   Lock file: {lock_file}")
        fd.close()
        return None, False
    fd.truncate(0)
    fd.write(str(os.getpid()))
    fd.flush()
    return fd, True


def release_lock(fd):
    """Release PID lock."""
    lock_file = _lock_path()
    try:
        fd.close()
        lock_file.unlink()
    except FileNotFoundError:
        pass


def _serve_dashboard(port: int):
    """Start HTTP server for dashboard in a daemon thread."""
    from .metrics.dashboard import generate_dashboard

    path = generate_dashboard()
    serve_dir = str(Path(path).parent)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=serve_dir, **kwargs)
        def log_message(self, fmt, *args):
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"  📊 Dashboard: http://0.0.0.0:{port}")
    server.serve_forever()


def daemon_loop(config, dashboard_port=None):
    """
    Main daemon loop. Runs run_cycle() repeatedly.

    Args:
        config: ZsigaConfig from load_config()
        dashboard_port: if set, start dashboard HTTP server
    """
    from .pipeline.orchestrator import ZsigaOrchestrator

    state = DaemonState()

    def sigusr1_handler(signum, frame):
        state.paused = True
        print("\n⏸  PAUSE requested (SIGUSR1) — will pause after current cycle")

    def sigusr2_handler(signum, frame):
        state.paused = False
        print("\n▶  RESUME (SIGUSR2) — continuing")

    def shutdown_handler(signum, frame):
        state.shutdown = True
        print("\n🛑 SHUTDOWN requested — will exit after current cycle")

    signal.signal(signal.SIGUSR1, sigusr1_handler)
    signal.signal(signal.SIGUSR2, sigusr2_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    lock_fd, locked = acquire_lock()
    if not locked:
        sys.exit(1)

    print(f"⚡ zsiga daemon started (PID {os.getpid()})")
    print(f"   Cycle interval: {config.pipeline.cycle_interval_hours}h")
    print(f"   Lock: {_lock_path()}")

    if dashboard_port:
        t = Thread(target=_serve_dashboard, args=(dashboard_port,), daemon=True)
        t.start()

    try:
        cycle_count = 0
        started_at = datetime.now().isoformat()
        while not state.shutdown:
            if state.paused:
                print("  ⏸  Paused — waiting for SIGUSR2 to resume...")
                while state.paused and not state.shutdown:
                    time.sleep(5)
                if state.shutdown:
                    break

            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"zsiga daemon — cycle #{cycle_count} @ {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            _write_daemon_state(
                started_at=started_at,
                cycle=cycle_count,
                state="paused" if state.paused else "running",
            )

            orchestrator = ZsigaOrchestrator(config)
            try:
                asyncio.run(orchestrator.run_cycle())
            except Exception as e:
                print(f"❌ Cycle error: {e}")
                try:
                    from .memory.learn import record_lesson
                    record_lesson(
                        title=f"daemon cycle #{cycle_count} failed",
                        context=str(e),
                        takeaway="Unhandled exception in daemon cycle",
                        pattern_key="daemon.cycle_error",
                        source="daemon",
                    )
                except Exception:
                    pass
            finally:
                orchestrator.close()

            try:
                from .metrics.dashboard import generate_dashboard
                generate_dashboard()
            except Exception:
                pass

            if state.shutdown:
                break

            # Idle state between cycles
            _write_daemon_state(
                started_at=started_at,
                cycle=cycle_count,
                state="running",
                current_change=None,
                current_phase=None,
                current_project=None,
            )

            interval = config.pipeline.cycle_interval_hours * 3600
            print(f"\n  💤 Next cycle in {config.pipeline.cycle_interval_hours}h...")

            slept = 0
            while slept < interval and not state.shutdown:
                if state.paused:
                    break
                time.sleep(min(30, interval - slept))
                slept += 30

    finally:
        _write_daemon_state(
            started_at=started_at,
            cycle=cycle_count,
            state="stopped",
            current_change=None,
            current_phase=None,
            current_project=None,
        )
        release_lock(lock_fd)
        print(f"\n⚡ zsiga daemon stopped (ran {cycle_count} cycles)")
