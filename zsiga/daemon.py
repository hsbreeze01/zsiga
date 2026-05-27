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
import sqlite3
import sys
import time
import asyncio
import fcntl
import subprocess
from pathlib import Path
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
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


def _scan_proposal_queue(changes_dir: Path | None = None) -> list[dict]:
    """Walk openspec/changes/ and return a list of proposal entries.

    Each entry: ``{name, project, summary}``. Summary is the first ``# ...``
    heading line extracted from ``proposal.md``.
    """
    if changes_dir is None:
        home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
        changes_dir = Path(home) / "openspec" / "changes"
    if not changes_dir.is_dir():
        return []
    queue: list[dict] = []
    for entry in sorted(changes_dir.iterdir()):
        if not entry.is_dir():
            continue
        proposal_md = entry / "proposal.md"
        if not proposal_md.exists():
            continue
        summary = ""
        try:
            for line in proposal_md.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("# "):
                    summary = stripped[2:].strip()
                    break
        except OSError:
            pass
        name = entry.name
        # Derive project from directory structure or config; fallback to name
        project = ""
        try:
            from .config import load_config

            cfg = load_config()
            for tgt_name, tc in cfg.targets.items():
                tgt_path = getattr(tc, "path", "")
                if tgt_path and str(changes_dir).startswith(str(tgt_path)):
                    project = tgt_name
                    break
        except Exception:
            pass
        if not project:
            project = name
        # Detect phase progress from output files
        has_clarify = (entry / "clarify.md").is_file()
        has_specs = (entry / "specs").is_dir() and any((entry / "specs").glob("*.md"))
        phase = "CLARIFY"
        if has_clarify:
            phase = "ENRICH"
        if has_specs:
            phase = "IMPLEMENT"
        # Detect lifecycle status from metrics
        lifecycle = "waiting"
        paused = False
        paused_reason = ""
        consecutive_fails = 0
        try:
            from .metrics.db import load_all_changes
            _all = load_all_changes()
            _mine = [c for c in _all if c.get("change_name") == name]
            if _mine:
                # Count consecutive fails from the end
                for c in reversed(_mine):
                    if c.get("outcome") in ("fail", "reverted"):
                        consecutive_fails += 1
                    else:
                        break
                last = _mine[-1]
                outcome = last.get("outcome", "")
                if outcome == "success":
                    lifecycle = "completed"
                elif consecutive_fails >= 3:
                    lifecycle = "paused"
                    paused = True
                    paused_reason = f"{consecutive_fails} consecutive failures"
                elif outcome in ("fail", "reverted"):
                    lifecycle = "stuck"
                else:
                    lifecycle = "active"
        except Exception:
            pass
        # Check manual .paused file
        paused_file = entry / ".paused"
        if paused_file.exists():
            paused = True
            if not paused_reason:
                paused_reason = "manual"
            lifecycle = "paused"
        queue.append({"name": name, "project": project, "summary": summary or "—", "phase": phase, "lifecycle": lifecycle, "paused": paused, "paused_reason": paused_reason, "consecutive_fails": consecutive_fails})
    return queue


def _compute_uptime_seconds(started_at: str | None) -> float | None:
    """Compute elapsed seconds since *started_at*, rounded to 1 decimal.

    Returns ``None`` when *started_at* is missing or cannot be parsed.
    """
    if not started_at:
        return None
    try:
        started_dt = datetime.fromisoformat(started_at)
    except (ValueError, TypeError):
        return None
    elapsed = (datetime.now() - started_dt).total_seconds()
    return round(elapsed, 1)


def _build_status_json() -> str:
    """Build the /api/status.json response payload."""
    # Daemon state with safe defaults
    ds = _read_daemon_state()
    daemon = {
        "pid": ds.get("pid"),
        "state": ds.get("state", "unknown"),
        "cycle": ds.get("cycle"),
        "current_change": ds.get("current_change"),
        "current_phase": ds.get("current_phase"),
        "current_project": ds.get("current_project"),
        "heartbeat": ds.get("last_heartbeat"),
        "uptime_seconds": _compute_uptime_seconds(ds.get("started_at")),
    }
    queue = _scan_proposal_queue()
    return json.dumps({"daemon": daemon, "queue": queue}, ensure_ascii=False)




def _build_metrics_json() -> str:
    """Build the /api/metrics.json response payload."""
    try:
        from .metrics.dashboard import compute_stats
        stats = compute_stats()
        summary = stats.get("summary", {})
        phases = stats.get("phases", {})
        return json.dumps({
            "summary": summary,
            "phases": phases,
            "rolling_rates": [],
        }, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _detect_proposal_phase(name: str) -> str:
    """Detect which phase a proposal has reached based on output files."""
    try:
        from .config import load_config
        from .transport import create_transport
        config = load_config()
        # Find the target and change_dir for this proposal
        for tname, tc in config.targets.items():
            transport = create_transport(tc)
            change_dir = f"{tc.change_root}/{name}"
            # Check clarify.md
            r = transport.run_shell(f"test -s '{change_dir}/clarify.md'", timeout=5)
            if r["exit_code"] != 0:
                return "CLARIFY"
            # Check specs
            r = transport.run_shell(f"ls '{change_dir}/specs'/*.md 2>/dev/null | head -1", timeout=5)
            if r["exit_code"] != 0 or not r["stdout"].strip():
                return "ENRICH"
            # Check implementation (feat commit)
            r = transport.run_shell(
                f"git log --oneline --all --grep='feat.*{name}' -1",
                timeout=5,
            )
            if r["exit_code"] != 0 or not r["stdout"].strip():
                return "IMPLEMENT"
            return "REVIEW"
    except Exception:
        pass
    return "CLARIFY"


def _build_current_json() -> str:
    """Build the /api/current.json response payload."""
    ds = _read_daemon_state()
    daemon_info = {
        "pid": ds.get("pid"),
        "state": ds.get("state", "unknown"),
        "cycle": ds.get("cycle"),
        "started_at": ds.get("started_at"),
        "heartbeat": ds.get("last_heartbeat"),
        "total_cycles": ds.get("total_cycles", 0),
        "idle_cycles": ds.get("idle_cycles", 0),
    }
    current = {
        "change": ds.get("current_change"),
        "phase": ds.get("current_phase"),
        "project": ds.get("current_project"),
    }
    # Phase progress for the progress bar
    phases_all = ["CLARIFY", "ENRICH", "IMPLEMENT", "REVIEW", "VERIFY", "DELIVER"]
    phase_progress = []
    cur_phase = ds.get("current_phase")
    found = False
    for p in phases_all:
        if p == cur_phase:
            found = True
            phase_progress.append({"name": p, "status": "active"})
        elif not found:
            phase_progress.append({"name": p, "status": "done"})
        else:
            phase_progress.append({"name": p, "status": "pending"})
    current["phase_progress"] = phase_progress
    queue = _scan_proposal_queue()
    # Phase status already in queue items from _scan_proposal_queue
    return json.dumps({
        "daemon": daemon_info,
        "current": current,
        "queue": queue,
    }, ensure_ascii=False)


def _health_check(db_path: str) -> dict:
    """Perform a lightweight liveness probe against the SQLite database.

    Returns ``{"status": "healthy", "db_records": <int>}`` on success or
    ``{"status": "unhealthy", "error": "<message>"}`` on any failure.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=2)
        count = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
        return {"status": "healthy", "db_records": count}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}
    finally:
        if conn is not None:
            conn.close()




def _build_pipeline_status(db_path: str, base_path: str) -> dict:
    """Build real-time pipeline status for the active proposal.

    Combines daemon_state, phase_state file, and DB records to show
    detailed phase-by-phase progress.
    """
    import glob as _glob

    ALL_PHASES = ["PROPOSAL_GATE", "CLARIFY", "ENRICH", "DESIGN_GATE",
                  "IMPLEMENT", "REVIEW", "VERIFY", "OPTIMIZE", "REFLECT", "DELIVER"]

    result = {"active_proposal": None, "current_phase": None,
              "phase_progress": [], "design_gate_attempts": 0,
              "judge_feedback": None, "queue": [], "daemon": {}}

    # 1. Daemon state
    ds = _read_daemon_state()
    result["daemon"] = {
        "state": ds.get("state", "unknown"),
        "cycle": ds.get("cycle", 0),
        "uptime_seconds": (datetime.now() - datetime.fromisoformat(ds["started_at"])).total_seconds() if ds.get("started_at") else 0,
        "total_changes_processed": ds.get("total_changes_processed", 0),
    }
    current = ds.get("current_change")

    # 2. Scan active proposals from openspec/changes/
    changes_dir = Path(base_path) / "openspec" / "changes"
    if changes_dir.exists():
        for d in sorted(changes_dir.iterdir()):
            if not d.is_dir() or d.name == "archive":
                continue
            pm = d / "proposal.md"
            if not pm.exists():
                continue
            name = d.name
            ps_file = d / ".phase_state"
            phase_state = {}
            if ps_file.exists():
                try:
                    phase_state = json.loads(ps_file.read_text())
                except Exception:
                    pass
            is_active = (current is not None and name == current) or (current is None and phase_state.get("current_phase"))
            result["queue"].append({
                "name": name,
                "current_phase": phase_state.get("current_phase"),
                "started_at": phase_state.get("started_at"),
                "is_active": bool(is_active),
            })
            if is_active and result["active_proposal"] is None:
                result["active_proposal"] = name
                result["current_phase"] = phase_state.get("current_phase")

    # 3. DB phases_json for completed phases
    active_name = result["active_proposal"]
    if active_name:
        try:
            conn = sqlite3.connect(db_path, timeout=2)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT phases_json FROM changes WHERE change_name = ? ORDER BY id DESC LIMIT 1",
                (active_name,))
            row = cur.fetchone()
            if row and row["phases_json"]:
                phases = json.loads(row["phases_json"])
                completed_phases = {p["phase"].upper(): p for p in phases}
            else:
                completed_phases = {}
            conn.close()
        except Exception:
            completed_phases = {}

        # 4. Build phase progress
        for phase in ALL_PHASES:
            normalized = {k.upper(): v for k, v in completed_phases.items()}
            if phase in normalized:
                p = completed_phases[phase]
                p = normalized[phase]
                entry = {"phase": phase, "status": "PASS" if p.get("outcome") == "success" else p.get("outcome", "DONE"),
                         "duration_s": round(p.get("seconds_used", 0), 1),
                         "llm_calls": p.get("llm_calls", 0),
                         "tokens": p.get("prompt_tokens", 0) + p.get("completion_tokens", 0)}
                if phase == "PROPOSAL_GATE" and p.get("detail"):
                    entry["score"] = p["detail"]
                result["phase_progress"].append(entry)
            elif phase == "PROPOSAL_GATE" and normalized:
                result["phase_progress"].append({"phase": phase, "status": "PASS"})
            elif phase == result["current_phase"].upper() if result["current_phase"] else False:
                elapsed = 0
                ps_data = {}
                ps_file = changes_dir / active_name / ".phase_state"
                if ps_file.exists():
                    try:
                        ps_data = json.loads(ps_file.read_text())
                        if ps_data.get("started_at"):
                            elapsed = round((datetime.now() - datetime.fromisoformat(ps_data["started_at"])).total_seconds(), 1)
                    except Exception:
                        pass
                result["phase_progress"].append({"phase": phase, "status": "RUNNING", "elapsed_s": elapsed})
            else:
                result["phase_progress"].append({"phase": phase, "status": "PENDING"})

    return result

def _build_proposal_stats_json(db_path: str) -> dict:
    """Query the changes table and return aggregate statistics.

    Returns a dict with keys: total, by_outcome, avg_duration_seconds, recent.
    On error, returns a dict with a single ``"error"`` key.
    """
    p = Path(db_path)
    if not p.exists():
        return {"error": f"Database file not found: {db_path}"}
    conn = None
    try:
        conn = sqlite3.connect(str(p))
        conn.row_factory = sqlite3.Row
        # Check that the changes table exists
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='changes'"
        ).fetchall()
        if not tables:
            return {"error": "changes table does not exist in database"}

        # Total count
        total = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]

        # Group by outcome
        rows = conn.execute(
            "SELECT outcome, COUNT(*) AS cnt FROM changes GROUP BY outcome"
        ).fetchall()
        by_outcome = {r["outcome"]: r["cnt"] for r in rows}

        # Average duration (only rows with non-empty finished_at)
        avg_row = conn.execute(
            """SELECT AVG(
                (julianday(finished_at) - julianday(started_at)) * 86400
            ) AS avg_dur
            FROM changes
            WHERE finished_at IS NOT NULL AND finished_at != ''
            """
        ).fetchone()
        avg_duration_seconds = avg_row["avg_dur"]
        if avg_duration_seconds is not None:
            avg_duration_seconds = round(avg_duration_seconds, 3)

        # Recent 5 entries ordered by id descending
        recent_rows = conn.execute(
            """SELECT change_name, outcome, started_at, finished_at
               FROM changes ORDER BY id DESC LIMIT 5"""
        ).fetchall()
        recent = [
            {
                "change_name": r["change_name"],
                "outcome": r["outcome"],
                "started_at": r["started_at"],
                "finished_at": r["finished_at"],
            }
            for r in recent_rows
        ]
        return {
            "total": total,
            "by_outcome": by_outcome,
            "avg_duration_seconds": avg_duration_seconds,
            "recent": recent,
        }
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        if conn is not None:
            conn.close()


def _build_proposal_detail(db_path: str, base_path: str, proposal_name: str) -> dict:
    """Return detailed info for a single proposal: files + DB phases + state."""
    result = {"proposal_name": proposal_name, "files": {}, "phases": [], "phase_state": None}

    # Read change_dir files
    changes_dir = Path(base_path) / "openspec" / "changes"
    change_dir = changes_dir / proposal_name
    if not change_dir.exists():
        for archive_sub in (changes_dir / "archive").iterdir():
            if archive_sub.is_dir() and archive_sub.name.endswith(f"-{proposal_name}"):
                change_dir = archive_sub
                break
    if not change_dir.exists():
        result["error"] = f"Proposal directory not found: {proposal_name}"
        return result

    result["change_dir"] = str(change_dir)

    # Read known diagnostic files
    diag_files = [
        "proposal.md", "clarify.md", "steward-review.md",
        "judge-feedback.md", "review.md", "reflect.md",
    ]
    for fname in diag_files:
        fpath = change_dir / fname
        if fpath.exists():
            try:
                result["files"][fname] = fpath.read_text()[:8000]
            except Exception:
                pass

    # Read specs/ if exists
    specs_dir = change_dir / "specs"
    if specs_dir.exists():
        for sp in sorted(specs_dir.glob("*.md")):
            try:
                result["files"][f"specs/{sp.name}"] = sp.read_text()[:8000]
            except Exception:
                pass

    # Read .phase_state
    ps_path = change_dir / ".phase_state"
    if ps_path.exists():
        try:
            result["phase_state"] = json.loads(ps_path.read_text())
        except Exception:
            pass

    # Read DB phases_json
    p = Path(db_path)
    if p.exists():
        conn = None
        try:
            conn = sqlite3.connect(str(p))
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM changes WHERE change_name = ? ORDER BY id DESC LIMIT 1",
                (proposal_name,),
            ).fetchone()
            if row:
                result["db_record"] = {
                    "id": row["id"],
                    "outcome": row["outcome"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                }
                phases_json = row["phases_json"]
                if phases_json:
                    result["phases"] = json.loads(phases_json)
        except Exception as exc:
            result["db_error"] = str(exc)
        finally:
            if conn:
                conn.close()

    return result


def _build_budget_analysis_json(db_path: str, home: str) -> dict:
    from .metrics.budget_analyzer import compute_budget_analysis, get_phase_budget_from_config
    from .config import load_config
    config_path = os.path.join(home, "zsiga.yaml")
    config_budgets = None
    try:
        cfg = load_config(config_path)
        config_budgets = get_phase_budget_from_config(cfg)
    except Exception:
        pass
    return compute_budget_analysis(db_path, config_budgets)


def _serve_dashboard(port: int):
    """Start HTTP server for dashboard in a daemon thread."""
    from .metrics.dashboard import generate_dashboard

    path = generate_dashboard(output_path="/tmp/zsiga-dashboard/dashboard.html")
    serve_dir = str(Path(path).parent)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=serve_dir, **kwargs)

        def _send_json(self, payload: str, status: int = 200):
            body = payload.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json_error(self, message: str):
            self._send_json(json.dumps({"error": message}), status=500)

        def do_GET(self):
            if self.path == "/api/status.json":
                self._send_json(_build_status_json())
            elif self.path == "/api/metrics.json":
                self._send_json(_build_metrics_json())
            elif self.path == "/api/current.json":
                self._send_json(_build_current_json())
            elif self.path == "/api/health":
                from .metrics.db import _DB_PATH
                result = _health_check(str(_DB_PATH))
                if result["status"] == "healthy":
                    result["timestamp"] = datetime.utcnow().strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    self._send_json(json.dumps(result), status=200)
                else:
                    self._send_json(json.dumps(result), status=503)
            elif self.path == "/api/pipeline-status":
                from .metrics.db import _DB_PATH
                home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
                result = _build_pipeline_status(str(_DB_PATH), home)
                self._send_json(json.dumps(result))
            elif self.path == "/api/proposal-stats":
                from .metrics.db import _DB_PATH
                result = _build_proposal_stats_json(str(_DB_PATH))
                if "error" in result:
                    self._send_json_error(result["error"])
                else:
                    self._send_json(json.dumps(result))
            elif self.path.startswith("/api/proposal/"):
                from .metrics.db import _DB_PATH
                proposal_name = self.path[len("/api/proposal/"):]
                proposal_name = proposal_name.rstrip("/")
                if not proposal_name:
                    self._send_json_error("Proposal name required")
                else:
                    home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
                    result = _build_proposal_detail(str(_DB_PATH), home, proposal_name)
                    self._send_json(json.dumps(result))
            elif self.path == "/api/budget-analysis":
                from .metrics.db import _DB_PATH
                home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
                result = _build_budget_analysis_json(str(_DB_PATH), home)
                self._send_json(json.dumps(result))
            elif self.path in ("/", "/dashboard", "/dashboard.html"):
                dashboard_path = Path("/tmp/zsiga-dashboard/dashboard.html")
                if dashboard_path.exists():
                    body = dashboard_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self._send_json(json.dumps({
                        "status": "running",
                        "message": "Dashboard not generated yet. Visit /api/status for JSON.",
                    }))
            else:
                super().do_GET()

        def log_message(self, fmt, *args):
            pass

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
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

                # Self-heal: verify zsiga package integrity before restart
                home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
                try:
                    import subprocess as _sp
                    verify_cmd = f"cd {home} && . venv/bin/activate && python3 -c 'import zsiga; print(\"OK\")'"
                    vr = _sp.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if vr.returncode != 0 or "OK" not in (vr.stdout or ""):
                        print(f"  ⚠️ Self-heal: zsiga import failed, reverting last commit")
                        _sp.run(f"cd {home} && git reset --hard HEAD~1", shell=True, check=False)
                        from .memory.learn import record_lesson
                        record_lesson(
                            title="Self-heal: reverted breaking change",
                            context=f"import check failed after delivery: {vr.stderr[:200]}",
                            takeaway="Evolution proposal introduced breaking change; auto-reverted",
                            pattern_key="evolution.self_heal.revert",
                            source="daemon",
                            case={"stderr": vr.stderr[:300] if vr.stderr else ""},
                            why="LLM-generated code can introduce import errors or circular deps",
                            rule="Always verify import integrity after self-modification before restart",
                        )
                except Exception as heal_err:
                    print(f"  ⚠️ Self-heal check error: {heal_err}")

                # Auto-restart: reload new code after successful delivery
                print("  🔄 Auto-restarting daemon to reload delivered code...")
                _write_daemon_state(
                    started_at=started_at,
                    cycle=cycle_count,
                    state="restarting",
                    total_cycles=total_cycles,
                    total_changes_processed=total_changes_processed,
                    idle_cycles=idle_cycles,
                    continuous_busy_cycles=continuous_busy_cycles,
                    last_change_at=last_change_at,
                )
                release_lock(lock_fd)
                subprocess.run(["sudo", "systemctl", "restart", "zsiga-daemon"], check=False)
            else:
                idle_cycles += 1
                continuous_busy_cycles = 0

            # Self-evolution engine: runs during designated evolution windows
            evo_ran = False
            if processed_count == 0:
                try:
                    from .intake.evolution import EvolutionEngine, EvolutionConfig
                    home = os.environ.get("ZSIGA_HOME", str(Path(__file__).resolve().parent.parent))
                    pcfg = config.pipeline
                    evo_config = EvolutionConfig(
                        enabled=pcfg.evolution_enabled,
                        window_start_hour=pcfg.evolution_window_start_hour,
                        window_end_hour=pcfg.evolution_window_end_hour,
                        max_proposals_per_window=pcfg.evolution_max_proposals,
                        min_cycle_gap_minutes=pcfg.evolution_min_gap_minutes,
                    )
                    engine = EvolutionEngine(home, evo_config)
                    if engine.should_evolve():
                        evo_path = engine.run_evolution_cycle()
                        if evo_path:
                            print(f"  🧬 Evolution generated proposal: {evo_path}")
                            evo_ran = True
                            continue
                except Exception as e:
                    print(f"  ⚠️ EvolutionEngine error: {e}")

            # Legacy Reflector: generate proposals from internal signals
            # when daemon has been idle for sustained periods
            if idle_cycles >= 3 and processed_count == 0 and not evo_ran:
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
                generate_dashboard(output_path="/tmp/zsiga-dashboard/dashboard.html")
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