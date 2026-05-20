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


def _read_daemon_state():
    """Read existing daemon_state.json or return empty dict."""
    path = _daemon_state_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_daemon_state(
    started_at: str,
    cycle: int,
    state: str = "running",
    current_change: str | None = None,
    current_phase: str | None = None,
    current_project: str | None = None,
    total_cycles: int | None = None,
    total_changes_processed: int | None = None,
    idle_cycles: int | None = None,
    continuous_busy_cycles: int | None = None,
    last_change_at: str | None = None,
):
    """Write daemon_state.json with current daemon status and scheduling stats."""
    existing = _read_daemon_state()
    data = {
        "pid": os.getpid(),
        "started_at": started_at,
        "cycle": cycle,
        "state": state,
        "current_change": current_change,
        "current_phase": current_phase,
        "current_project": current_project,
        "last_heartbeat": datetime.now().isoformat(),
        "total_cycles": total_cycles if total_cycles is not None else existing.get("total_cycles", 0),
        "total_changes_processed": total_changes_processed if total_changes_processed is not None else existing.get("total_changes_processed", 0),
        "idle_cycles": idle_cycles if idle_cycles is not None else existing.get("idle_cycles", 0),
        "continuous_busy_cycles": continuous_busy_cycles if continuous_busy_cycles is not None else existing.get("continuous_busy_cycles", 0),
        "last_change_at": last_change_at if last_change_at is not None else existing.get("last_change_at"),
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
    print(f"   Idle poll: {config.pipeline.idle_poll_minutes}min")
    print(f"   Lock: {_lock_path()}")

    if dashboard_port:
        t = Thread(target=_serve_dashboard, args=(dashboard_port,), daemon=True)
        t.start()

    try:
        cycle_count = 0
        started_at = datetime.now().isoformat()

        # Initialize scheduling state from existing daemon_state or defaults
        prev_state = _read_daemon_state()
        total_cycles = prev_state.get("total_cycles", 0)
        total_changes_processed = prev_state.get("total_changes_processed", 0)
        idle_cycles = prev_state.get("idle_cycles", 0)
        continuous_busy_cycles = prev_state.get("continuous_busy_cycles", 0)
        last_change_at = prev_state.get("last_change_at")

        while not state.shutdown:
            if state.paused:
                print("  ⏸  Paused — waiting for SIGUSR2 to resume...")
                while state.paused and not state.shutdown:
                    time.sleep(5)
                if state.shutdown:
                    break

            cycle_count += 1
            total_cycles += 1
            print(f"\n{'='*60}")
            print(f"zsiga daemon — cycle #{cycle_count} @ {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            _write_daemon_state(
                started_at=started_at,
                cycle=cycle_count,
                state="paused" if state.paused else "running",
                total_cycles=total_cycles,
                total_changes_processed=total_changes_processed,
                idle_cycles=idle_cycles,
                continuous_busy_cycles=continuous_busy_cycles,
                last_change_at=last_change_at,
            )

            orchestrator = None
            processed_count = 0
            try:
                orchestrator = ZsigaOrchestrator(config)
                processed_count = asyncio.run(orchestrator.run_cycle())
            except Exception as e:
                print(f"❌ Cycle error: {e}")
                try:
                    from .memory.learn import record_lesson
                    import traceback as _tb
                    tb_excerpt = _tb.format_exc()[:500]
                    exc_type = type(e).__name__
                    transient_types = (ConnectionError, TimeoutError, OSError)
                    tag = "[transient]" if isinstance(e, transient_types) else "[permanent]"
                    record_lesson(
                        title=f"daemon cycle #{cycle_count} failed",
                        context=f"type={exc_type}, tb={tb_excerpt}, cycle={cycle_count}",
                        takeaway=f"{tag} {exc_type}: {e}",
                        pattern_key="daemon.cycle_error",
                        source="daemon",
                    )
                except Exception:
                    pass
            finally:
                if orchestrator is not None:
                    orchestrator.close()

            # Update scheduling statistics
            total_changes_processed += processed_count
            if processed_count > 0:
                continuous_busy_cycles += 1
                idle_cycles = 0
                last_change_at = datetime.now().isoformat()
            else:
                idle_cycles += 1
                continuous_busy_cycles = 0

            # Self-reflection: generate proposals from internal signals
            # when daemon has been idle for sustained periods
            if idle_cycles >= 3 and processed_count == 0:
                try:
                    from .intake.reflector import Reflector
                    reflector = Reflector()
                    home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
                    proposals = reflector.run(home)
                    if proposals:
                        print(f"  🔄 Reflector generated {len(proposals)} proposal(s)")
                        continue
                except Exception as e:
                    print(f"  ⚠️ Reflector error: {e}")

            try:
                from .metrics.dashboard import generate_dashboard
                generate_dashboard()
            except Exception:
                pass

            if state.shutdown:
                break

            # Write idle state between cycles
            _write_daemon_state(
                started_at=started_at,
                cycle=cycle_count,
                state="running",
                current_change=None,
                current_phase=None,
                current_project=None,
                total_cycles=total_cycles,
                total_changes_processed=total_changes_processed,
                idle_cycles=idle_cycles,
                continuous_busy_cycles=continuous_busy_cycles,
                last_change_at=last_change_at,
            )

            # Smart scheduling: decide sleep duration
            max_cc = config.pipeline.max_continuous_cycles
            cooldown_mins = config.pipeline.cooldown_minutes
            idle_mins = config.pipeline.idle_poll_minutes

            if continuous_busy_cycles >= max_cc:
                # Safety valve: forced cooldown
                print(f"\n  ⚠️ Safety valve: {continuous_busy_cycles} consecutive busy cycles, "
                      f"cooling down for {cooldown_mins} minutes")
                interval = cooldown_mins * 60
                continuous_busy_cycles = 0
            elif processed_count > 0:
                # Immediate re-cycle
                print(f"\n  ⚡ Processed {processed_count} changes — immediate next cycle")
                continue
            elif idle_mins:
                # Idle poll
                interval = idle_mins * 60
                print(f"\n  💤 No changes — next poll in {idle_mins} minutes...")
            else:
                # Fallback to legacy cycle_interval_hours
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
