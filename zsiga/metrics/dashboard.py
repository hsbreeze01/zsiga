import json
from datetime import datetime
from pathlib import Path
from .collector import compute_stats, check_milestone, compute_rolling_rates
from .db import load_all_changes
from .types import ALL_MILESTONES
from ..memory.journal import load_journal

_DASHBOARD_PATH = Path(__file__).resolve().parent.parent.parent / "site" / "dashboard.html"
_MASCOT_SRC = Path(__file__).resolve().parent.parent.parent / "site" / "mascot.png"


def _detect_state(stats: dict) -> str:
    ts = stats.get("last_updated", "")
    if not ts:
        return "resting"
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
        return "working" if elapsed < 3600 else "resting"
    except (ValueError, TypeError):
        return "resting"


def _render_daemon_status() -> str:
    """Read data/daemon_state.json and return HTML card row for daemon status."""
    base = Path(__file__).resolve().parent.parent.parent
    state_path = base / "data" / "daemon_state.json"
    try:
        raw = state_path.read_text(encoding="utf-8")
        ds = json.loads(raw)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return (
            '<div class="grid" style="margin-bottom:1rem">'
            '<div class="card">'
            '<div class="label"> Daemon</div>'
            '<div class="value meta">Daemon offline</div>'
            "</div></div>\n"
        )

    pid = ds.get("pid", "—")
    started_at = ds.get("started_at", "—")
    cycle = ds.get("cycle", "—")
    daemon_state = ds.get("state", "unknown")
    current_change = ds.get("current_change")
    current_phase = ds.get("current_phase")
    last_heartbeat = ds.get("last_heartbeat", "—")

    if started_at and started_at != "—":
        started_at = started_at[:19].replace("T", " ")
    if last_heartbeat and last_heartbeat != "—":
        last_heartbeat = last_heartbeat[:19].replace("T", " ")

    state_cls = "working" if daemon_state == "running" else "resting"
    state_label = daemon_state.capitalize()

    processing = (
        f"{current_change} ({current_phase or '—'})"
        if current_change
        else "Idle"
    )

    return (
        f'<div class="grid" style="margin-bottom:1rem">'
        f'<div class="card"><div class="label"> Daemon</div>'
        f'<div class="value" style="font-size:1.2rem">{pid}</div></div>'
        f'<div class="card"><div class="label"> Started At</div>'
        f'<div class="value" style="font-size:1rem">{started_at}</div></div>'
        f'<div class="card"><div class="label"> Cycle</div>'
        f'<div class="value" style="font-size:1.2rem">{cycle}</div></div>'
        f'<div class="card"><div class="label"> State</div>'
        f'<span class="state-badge {state_cls}">{state_label}</span></div>'
        f'<div class="card"><div class="label"> Processing</div>'
        f'<div class="meta" style="font-size:0.85rem;margin-top:0.3rem">'
        f"{processing}</div></div>"
        f'<div class="card"><div class="label"> Heartbeat</div>'
        f'<div class="meta" style="font-size:0.85rem;margin-top:0.3rem">'
        f"{last_heartbeat}</div></div>"
        f"</div>\n"
    )


def _render_failure_diagnosis() -> str:
    """Scan for failed changes and render diagnosis panel."""
    changes = load_all_changes()
    failed = [c for c in changes if c.get("outcome") == "reverted"]

    if not failed:
        return (
            '<div class="section"><h2>🔍 Failure Diagnosis</h2>'
            '<div class="meta">No failures recorded</div></div>\n'
        )

    # Load learnings
    base_dir = Path(__file__).resolve().parent.parent.parent
    learnings_path = base_dir / "memory" / "learnings.jsonl"
    lessons: list[dict] = []
    if learnings_path.exists():
        for line in learnings_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                lessons.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue

    entries_html = ""
    for c in reversed(failed[-10:]):
        name = c.get("change_name", "—")
        project = c.get("project", "—")

        # Find the failed phase (last non-success phase)
        failed_phase = "—"
        for p in c.get("phases", []):
            if p.get("outcome") != "success":
                failed_phase = p.get("phase", "—")

        # Find matching lesson
        takeaway = ""
        for lesson in reversed(lessons):
            pk = lesson.get("pattern_key", "")
            title = lesson.get("title", "")
            if pk.startswith("pipeline.fail") or pk.startswith("code."):
                if name in title:
                    takeaway = lesson.get("takeaway", "")[:200]
                    break

        # Duration
        started = c.get("started_at", "")
        finished = c.get("finished_at", "")
        duration = "—"
        if started and finished:
            try:
                s_dt = datetime.fromisoformat(started)
                f_dt = datetime.fromisoformat(finished)
                duration = _fmt_seconds((f_dt - s_dt).total_seconds())
            except (ValueError, TypeError):
                pass

        ts = started[:16].replace("T", " ") if started else "—"

        # Diagnosis content from file
        diagnosis_html = ""
        for dpath in [
            base_dir / "openspec" / "changes" / name / "diagnosis.md",
            base_dir / "openspec" / "changes" / "archive" / name / "diagnosis.md",
        ]:
            if dpath.exists():
                diag_text = dpath.read_text(encoding="utf-8").strip()
                if diag_text:
                    escaped = (
                        diag_text.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br>")
                    )
                    diagnosis_html = (
                        '<div style="font-size:0.8rem;color:#94a3b8;'
                        "margin-top:0.5rem;padding:0.5rem;"
                        'background:#0f172a;border-radius:4px">'
                        f"{escaped}</div>"
                    )
                break

        takeaway_html = ""
        if takeaway:
            esc_tw = (
                takeaway.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            takeaway_html = (
                '<div style="font-size:0.8rem;color:#f59e0b;'
                f'margin-top:0.3rem">{esc_tw}</div>'
            )

        entries_html += (
            "<details><summary "
            'style="cursor:pointer;padding:0.4rem 0.8rem;'
            'background:#1e293b;border-radius:4px;font-size:0.85rem">'
            f"<strong>{name}</strong> · {project} · "
            f"{failed_phase} · {duration} · {ts}"
            f"</summary>{takeaway_html}{diagnosis_html}"
            f"</details>\n"
        )

    return (
        '<div class="section">\n  <h2>🔍 Failure Diagnosis</h2>\n'
        f"  {entries_html}\n</div>\n"
    )


def _duration_bars_html(changes: list[dict]) -> str:
    """Render pure-CSS bar chart of recent change durations."""
    completed = [
        c for c in changes if c.get("outcome") in ("success", "reverted")
    ]
    if len(completed) < 2:
        return '<div class="meta">Insufficient data</div>'

    recent = completed[-20:]
    bars = []
    for c in recent:
        started = c.get("started_at", "")
        finished = c.get("finished_at", "")
        dur = 0.0
        if started and finished:
            try:
                s_dt = datetime.fromisoformat(started)
                f_dt = datetime.fromisoformat(finished)
                dur = (f_dt - s_dt).total_seconds()
            except (ValueError, TypeError):
                pass
        bars.append({"duration": dur, "outcome": c.get("outcome", "")})

    max_dur = max(b["duration"] for b in bars) if bars else 1
    if max_dur == 0:
        max_dur = 1

    html = '<div style="display:flex;align-items:flex-end;gap:2px;height:40px">'
    for b in bars:
        height_pct = (
            int(b["duration"] / max_dur * 100) if max_dur > 0 else 0
        )
        color = "#22c55e" if b["outcome"] == "success" else "#ef4444"
        html += (
            f'<div style="width:8px;height:{height_pct}%;'
            f"background:{color};border-radius:1px\" "
            f'title="{b["duration"]:.0f}s"></div>'
        )
    html += "</div>"
    return html


def generate_dashboard(output_path: str = None) -> str:
    stats = compute_stats()
    milestones = []
    for m_def in ALL_MILESTONES:
        milestones.append(check_milestone(stats, m_def))
    state = _detect_state(stats)
    html = _render(stats, milestones, state)

    out = Path(output_path) if output_path else _DASHBOARD_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)


def _render(stats: dict, milestones: list[dict], state: str = "resting") -> str:
    phase_rows = _phase_table(stats.get("phase_stats", {}))
    milestone_cards = ""
    for m in milestones:
        milestone_cards += _milestone_card(m) + "\n"
    recent = _recent_list(stats.get("recent_changes", []))
    usage_section = _usage_section(stats)
    journal = _journal_section()
    todo = _todo_section()
    mascot = _mascot_img(state)

    state_label = "⚡ Working" if state == "working" else "💤 Resting"

    current_level = _current_level(milestones)

    try:
        daemon_section = _render_daemon_status()
    except Exception:
        daemon_section = ""
    try:
        failure_section = _render_failure_diagnosis()
    except Exception:
        failure_section = ""
    try:
        _rates = compute_rolling_rates()
        sparkline_card = _sparkline_html(_rates)
    except Exception:
        sparkline_card = '<div class="meta">Insufficient data</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="60">
<title>zsiga dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #0f172a; color: #e2e8f0; padding: 2rem; }}
h1 {{ font-size: 1.5rem; margin-bottom: 1.5rem; }}
h1 span {{ color: #64748b; font-size: 0.9rem; font-weight: 400; margin-left: 0.5rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
         gap: 1rem; margin-bottom: 2rem; }}
.card {{ background: #1e293b; border-radius: 8px; padding: 1.2rem; }}
.card .label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;
               letter-spacing: 0.05em; margin-bottom: 0.4rem; }}
.card .value {{ font-size: 1.8rem; font-weight: 700; }}
.card .value.good {{ color: #22c55e; }}
.card .value.warn {{ color: #f59e0b; }}
.card .value.bad {{ color: #ef4444; }}
.section {{ margin-bottom: 2rem; }}
.section h2 {{ font-size: 1.1rem; margin-bottom: 0.8rem; color: #94a3b8; }}
table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px;
         overflow: hidden; }}
th, td {{ padding: 0.6rem 1rem; text-align: left; font-size: 0.85rem; }}
th {{ background: #334155; color: #94a3b8; font-weight: 600; }}
td {{ border-top: 1px solid #334155; }}
.milestone {{ background: #1e293b; border-radius: 8px; padding: 1.2rem;
              border-left: 4px solid; margin-bottom: 1rem; }}
.milestone h3 {{ font-size: 1rem; margin-bottom: 0.8rem; }}
.criterion {{ display: flex; align-items: center; gap: 0.5rem;
              padding: 0.3rem 0; font-size: 0.85rem; }}
.criterion .icon {{ width: 18px; text-align: center; }}
.progress {{ flex: 1; height: 6px; background: #334155; border-radius: 3px;
             overflow: hidden; max-width: 200px; }}
.progress .fill {{ height: 100%; border-radius: 3px; transition: width 0.3s; }}
.meta {{ font-size: 0.75rem; color: #64748b; margin-top: 0.3rem; }}
.recent {{ list-style: none; padding: 0; }}
.recent li {{ padding: 0.3rem 0; font-size: 0.85rem; color: #94a3b8; }}
.recent li::before {{ content: "→"; margin-right: 0.5rem; color: #475569; }}
.hero {{ display: flex; align-items: center; gap: 2rem; margin-bottom: 2rem; }}
.hero-mascot {{ flex-shrink: 0; }}
.hero-info {{ flex: 1; }}
.hero-info h1 {{ margin-bottom: 0.5rem; }}
.state-badge {{ display: inline-block; padding: 0.2rem 0.8rem; border-radius: 999px;
               font-size: 0.8rem; font-weight: 600; margin-top: 0.3rem; }}
.state-badge.working {{ background: #065f4620; color: #34d399; border: 1px solid #34d39940; }}
.state-badge.resting {{ background: #1e3a5f20; color: #7dd3fc; border: 1px solid #7dd3fc40; }}
@keyframes breathe {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.03); }} }}
@keyframes coding {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-2px); }} }}
.mascot-working {{ animation: coding 1.5s ease-in-out infinite; }}
.mascot-resting {{ animation: breathe 3s ease-in-out infinite; }}
@keyframes float-z {{ 0% {{ opacity: 1; transform: translateY(0); }} 100% {{ opacity: 0; transform: translateY(-18px); }} }}
.float-z {{ animation: float-z 2s ease-in infinite; }}
.float-z2 {{ animation: float-z 2s ease-in 0.6s infinite; }}
.float-z3 {{ animation: float-z 2s ease-in 1.2s infinite; }}
@keyframes spark {{ 0%,100% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} }}
.spark1 {{ animation: spark 1.2s ease-in-out infinite; }}
.spark2 {{ animation: spark 1.2s ease-in-out 0.4s infinite; }}
.spark3 {{ animation: spark 1.2s ease-in-out 0.8s infinite; }}
.journal {{ display: flex; flex-direction: column; gap: 0.6rem; }}
.journal-entry {{ background: #1e293b; border-radius: 6px; padding: 0.7rem 1rem; }}
.journal-header {{ display: flex; align-items: flex-start; gap: 0.5rem; font-size: 0.88rem; line-height: 1.5; }}
.journal-text {{ flex: 1; }}
.journal-meta {{ font-size: 0.72rem; color: #64748b; margin-top: 0.25rem; }}
</style>
</head>
<body>

<div style="text-align:right;font-size:0.75rem;color:#64748b;margin-bottom:0.5rem">Auto-refresh: 60s</div>

<div class="hero">
  <div class="hero-mascot">
    {mascot}
  </div>
  <div class="hero-info">
    <h1>zsiga <span>{current_level}</span></h1>
    <span class="state-badge {state}">{state_label}</span>
  </div>
</div>

{daemon_section}

<div class="grid">
  <div class="card">
    <div class="label">🪙 Total Changes</div>
    <div class="value">{stats['total_changes']}</div>
  </div>
  <div class="card">
    <div class="label">🎯 Hit Rate</div>
    <div class="value {_rate_class(stats['success_rate_pct'])}">{stats['success_rate_pct']}%</div>
    <div class="meta">{stats['successful_changes']} hit / {stats['failed_changes']} miss</div>
  </div>
  <div class="card">
    <div class="label">📐 Targets</div>
    <div class="value">{stats['distinct_projects']}</div>
    <div class="meta">{', '.join(stats['projects']) if stats['projects'] else '—'}</div>
  </div>
  <div class="card">
    <div class="label">📝 Lessons</div>
    <div class="value">{stats['lessons_learned']}</div>
  </div>
  <div class="card">
    <div class="label">⚡ First-Pass Rate</div>
    <div class="value {_rate_class(stats['first_pass_test_rate_pct'])}">{stats['first_pass_test_rate_pct']}%</div>
  </div>
  <div class="card">
    <div class="label">✅ Verify Rate</div>
    <div class="value {_rate_class(stats['verify_pass_rate_pct'])}">{stats['verify_pass_rate_pct']}%</div>
  </div>
  <div class="card">
    <div class="label">🗜️ Compactions</div>
    <div class="value">{stats.get('total_compaction_count', 0)}</div>
    <div class="meta">electromagnetic compress</div>
  </div>
  <div class="card">
    <div class="label">🐾 Sub-Agents</div>
    <div class="value">{stats.get('total_sub_agent_count', 0)}</div>
    <div class="meta">network dispatched</div>
  </div>
</div>

<div class="grid" style="margin-bottom:2rem">
  <div class="card">
    <div class="label">📈 Success Rate Trend</div>
    {sparkline_card}
  </div>
</div>

<div class="section">
    <h2>⚡ Phase Performance</h2>
  {phase_rows}
</div>

{failure_section}

{usage_section}

<div class="section">
    <h2>🪙 Evolution Roadmap</h2>
  {milestone_cards}
</div>

{todo}

{journal}

<div class="section">
  <h2>Recent Changes</h2>
  <ul class="recent">
    {recent}
  </ul>
</div>

<div class="meta" style="margin-top:2rem">Updated: {stats['last_updated']}</div>
</body>
</html>"""


def _mascot_img(state: str = "resting") -> str:
    return _pixel_misaka(state)


def _pixel_misaka(state: str = "resting") -> str:
    cls = "mascot-working" if state == "working" else "mascot-resting"
    s = 4  # pixel scale

    def px(x, y, color, w=1, h=1):
        return f'<rect x="{x*s}" y="{y*s}" width="{w*s}" height="{h*s}" fill="{color}"/>'

    def pxa(x, y, color, opacity, w=1, h=1):
        return f'<rect x="{x*s}" y="{y*s}" width="{w*s}" height="{h*s}" fill="{color}" opacity="{opacity}"/>'

    HAIR_DARK = "#5b21b6"
    HAIR_MID = "#7c3aed"
    HAIR_LIGHT = "#a78bfa"
    SKIN = "#fde68a"
    SKIN_SHADOW = "#d4a44a"
    EYE = "#7c3aed"
    EYE_HI = "#c4b5fd"
    BLUSH = "#fda4af"
    MOUTH = "#92400e"
    WHITE_TOP = "#e2e8f0"
    UNIFORM = "#7c3aed"
    SKIRT = "#4c1d95"
    SHOE = "#1e1b4b"
    COIN_GOLD = "#f59e0b"
    COIN_DARK = "#d97706"
    COIN_HI = "#fde68a"
    SPARK_Y = "#fbbf24"
    SPARK_P = "#c4b5fd"
    CLIP_G = "#22c55e"
    CLIP_D = "#16a34a"

    rows = []

    # === HAIR BACK (wide block) ===
    for x in range(9, 24):
        rows.append(px(x, 4, HAIR_DARK))
    for x in range(8, 25):
        rows.append(px(x, 5, HAIR_DARK))
    for x in range(8, 25):
        rows.append(px(x, 6, HAIR_DARK))
    for x in range(7, 26):
        rows.append(px(x, 7, HAIR_DARK))
    # hair strands flowing right
    for x in range(24, 27):
        rows.append(px(x, 6, HAIR_MID))
    for x in range(25, 28):
        rows.append(px(x, 5, HAIR_MID))
    for x in range(27, 29):
        rows.append(px(x, 7, HAIR_LIGHT, 0.7))
    for x in range(26, 28):
        rows.append(px(x, 8, HAIR_LIGHT, 0.5))

    # === FACE ===
    for y in range(8, 16):
        for x in range(10, 23):
            rows.append(px(x, y, SKIN))
    # face shadow right
    rows.append(px(22, 8, SKIN_SHADOW))
    rows.append(px(22, 9, SKIN_SHADOW))
    rows.append(px(22, 13, SKIN_SHADOW))
    rows.append(px(22, 14, SKIN_SHADOW))
    rows.append(px(22, 15, SKIN_SHADOW))

    # === HAIR BANGS (over face) ===
    for x in range(9, 24):
        rows.append(px(x, 8, HAIR_DARK))
    for x in range(9, 14):
        rows.append(px(x, 9, HAIR_DARK))
    for x in range(16, 18):
        rows.append(px(x, 9, HAIR_DARK))
    for x in range(20, 24):
        rows.append(px(x, 9, HAIR_MID))
    # side hair left
    for y in range(9, 15):
        rows.append(px(8, y, HAIR_DARK))
        rows.append(px(9, y, HAIR_DARK, 0.5))

    # === HAIR CLIP (Gekota) ===
    rows.append(px(10, 9, CLIP_G, 1, 2))
    rows.append(px(11, 9, CLIP_D, 1, 1))

    # === EYES ===
    # left eye
    rows.append(px(12, 10, WHITE_TOP))
    rows.append(px(13, 10, WHITE_TOP))
    rows.append(px(12, 11, EYE))
    rows.append(px(13, 11, EYE))
    rows.append(px(14, 11, EYE_HI))
    rows.append(px(12, 12, EYE))
    rows.append(px(13, 12, EYE))
    # right eye
    rows.append(px(18, 10, WHITE_TOP))
    rows.append(px(19, 10, WHITE_TOP))
    rows.append(px(18, 11, EYE))
    rows.append(px(19, 11, EYE))
    rows.append(px(20, 11, EYE_HI))
    rows.append(px(18, 12, EYE))
    rows.append(px(19, 12, EYE))

    # === BLUSH ===
    rows.append(pxa(11, 13, BLUSH, 0.5))
    rows.append(pxa(20, 13, BLUSH, 0.5))

    # === MOUTH ===
    if state == "working":
        rows.append(px(15, 14, MOUTH))
        rows.append(px(16, 14, MOUTH))
    else:
        rows.append(pxa(15, 14, MOUTH, 0.7))
        rows.append(pxa(16, 14, MOUTH, 0.7))

    # === BODY (uniform top) ===
    for y in range(16, 21):
        for x in range(11, 22):
            rows.append(px(x, y, UNIFORM))
    # white collar
    for x in range(14, 19):
        rows.append(px(x, 16, WHITE_TOP))
    # collar V
    rows.append(px(15, 17, WHITE_TOP))
    rows.append(px(17, 17, WHITE_TOP))
    rows.append(px(16, 18, WHITE_TOP))

    # === ARMS ===
    # left arm (down)
    for y in range(18, 22):
        rows.append(px(10, y, UNIFORM))
        rows.append(px(9, y, UNIFORM))
    # right arm (reaching right — coin flick pose)
    for y in range(17, 19):
        rows.append(px(22, y, UNIFORM))
        rows.append(px(23, y, UNIFORM))
    for y in range(15, 17):
        rows.append(px(24, y, UNIFORM))
        rows.append(px(25, y, UNIFORM))
    # hand
    rows.append(px(26, 14, SKIN))
    rows.append(px(27, 14, SKIN))
    rows.append(px(26, 15, SKIN))

    # === SKIRT ===
    for y in range(21, 25):
        for x in range(10, 23):
            rows.append(px(x, y, SKIRT))

    # === LEGS ===
    for y in range(25, 28):
        rows.append(px(13, y, SKIN))
        rows.append(px(14, y, SKIN))
        rows.append(px(19, y, SKIN))
        rows.append(px(20, y, SKIN))

    # === SHOES ===
    rows.append(px(12, 28, SHOE))
    rows.append(px(13, 28, SHOE))
    rows.append(px(14, 28, SHOE))
    rows.append(px(18, 28, SHOE))
    rows.append(px(19, 28, SHOE))
    rows.append(px(20, 28, SHOE))

    # === COIN ===
    if state == "working":
        coin_x, coin_y = 29, 10
        rows.append(px(coin_x, coin_y, COIN_HI))
        rows.append(px(coin_x+1, coin_y, COIN_GOLD))
        rows.append(px(coin_x+2, coin_y, COIN_GOLD))
        rows.append(px(coin_x, coin_y+1, COIN_GOLD))
        rows.append(px(coin_x+1, coin_y+1, COIN_DARK))
        rows.append(px(coin_x+2, coin_y+1, COIN_GOLD))
        rows.append(px(coin_x, coin_y+2, COIN_GOLD))
        rows.append(px(coin_x+1, coin_y+2, COIN_GOLD))
        rows.append(px(coin_x+2, coin_y+2, COIN_HI))

    # === ELECTRIC ARCS ===
    if state == "working":
        rows.append(px(28, 9, SPARK_Y))
        rows.append(px(29, 8, SPARK_Y))
        rows.append(px(31, 9, SPARK_P))
        rows.append(px(32, 8, SPARK_Y))
        rows.append(px(28, 13, SPARK_Y))
        rows.append(px(30, 14, SPARK_P))
        rows.append(px(31, 13, SPARK_Y))
        rows.append(px(25, 12, SPARK_P))
        rows.append(px(24, 13, SPARK_Y))
        rows.append(px(33, 11, SPARK_P))
        rows.append(px(34, 10, SPARK_Y))
        rows.append(px(33, 14, SPARK_Y))
        rows.append(px(27, 16, SPARK_P))
    else:
        rows.append(pxa(28, 10, SPARK_P, 0.3))
        rows.append(pxa(25, 13, SPARK_P, 0.2))

    # === LEVEL BADGE on skirt ===
    rows.append(px(13, 22, COIN_GOLD, 5, 1))
    rows.append(px(14, 22, COIN_GOLD, 1, 1))
    rows.append(px(15, 22, COIN_GOLD, 1, 1))
    rows.append(px(16, 22, COIN_GOLD, 1, 1))
    rows.append(px(17, 22, COIN_GOLD, 1, 1))

    pixel_art = "\n".join(rows)

    w = 38 * s
    h = 32 * s

    if state == "working":
        return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" class="{cls}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated;">
<rect width="{w}" height="{h}" fill="transparent"/>
{pixel_art}
</svg>"""

    zzz = ""
    if state == "resting":
        zzz = f"""<text x="{30*s}" y="{6*s}" font-size="14" fill="#a5b4fc" class="float-z" font-weight="700">z</text>
<text x="{33*s}" y="{4*s}" font-size="11" fill="#a5b4fc" class="float-z2" font-weight="700">z</text>
<text x="{35*s}" y="{3*s}" font-size="9" fill="#a5b4fc" class="float-z3" font-weight="700">z</text>"""

    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" class="{cls}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated;">
<rect width="{w}" height="{h}" fill="transparent"/>
{pixel_art}
{zzz}
</svg>"""


def _mascot_svg(state: str = "resting") -> str:
    cls = "mascot-working" if state == "working" else "mascot-resting"
    if state == "working":
        return f"""<svg width="160" height="160" viewBox="0 0 160 160" class="{cls}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="coinGrad" cx="35%" cy="30%" r="65%">
    <stop offset="0%" stop-color="#fde68a"/>
    <stop offset="40%" stop-color="#f59e0b"/>
    <stop offset="100%" stop-color="#d97706"/>
  </radialGradient>
  <radialGradient id="arcGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fbbf24"/>
    <stop offset="100%" stop-color="#7c3aed" stop-opacity="0"/>
  </radialGradient>
  <filter id="elecGlow">
    <feGaussianBlur stdDeviation="3" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="coinGlow">
    <feGaussianBlur stdDeviation="1.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- background ring -->
<circle cx="80" cy="80" r="70" fill="none" stroke="#7c3aed" stroke-width="1.5" opacity="0.15"/>
<circle cx="80" cy="80" r="55" fill="none" stroke="#7c3aed" stroke-width="0.8" opacity="0.1" stroke-dasharray="4 6"/>
<!-- outer arc lightning -->
<polyline points="25,60 40,40 55,65 70,30 85,55 100,25 115,50 130,35"
  stroke="#fbbf24" stroke-width="2.5" fill="none" filter="url(#elecGlow)" opacity="0.7" class="spark1"/>
<polyline points="30,100 50,120 65,90 80,130 95,100 110,125 125,95 135,110"
  stroke="#c4b5fd" stroke-width="2" fill="none" filter="url(#elecGlow)" opacity="0.5" class="spark2"/>
<!-- electric field lines radiating from center -->
<line x1="80" y1="80" x2="20" y2="30" stroke="#fbbf24" stroke-width="0.6" opacity="0.3" class="spark3"/>
<line x1="80" y1="80" x2="140" y2="35" stroke="#fbbf24" stroke-width="0.6" opacity="0.3" class="spark1"/>
<line x1="80" y1="80" x2="15" y2="110" stroke="#c4b5fd" stroke-width="0.5" opacity="0.25" class="spark2"/>
<line x1="80" y1="80" x2="145" y2="115" stroke="#c4b5fd" stroke-width="0.5" opacity="0.25" class="spark3"/>
<!-- THE COIN — centered, spinning -->
<ellipse cx="80" cy="72" rx="28" ry="28" fill="url(#coinGrad)" filter="url(#coinGlow)">
  <animateTransform attributeName="transform" type="rotate" from="0 80 72" to="360 80 72" dur="8s" repeatCount="indefinite"/>
</ellipse>
<ellipse cx="80" cy="72" rx="20" ry="20" fill="none" stroke="#d97706" stroke-width="1" opacity="0.5">
  <animateTransform attributeName="transform" type="rotate" from="0 80 72" to="360 80 72" dur="8s" repeatCount="indefinite"/>
</ellipse>
<!-- coin inner detail — ¥ symbol -->
<text x="80" y="80" font-size="24" fill="#92400e" text-anchor="middle" font-weight="900" font-family="serif" opacity="0.6">¥</text>
<!-- spec text on coin ring -->
<text x="80" y="68" font-size="6" fill="#d97706" text-anchor="middle" font-weight="700" letter-spacing="4" opacity="0.5">SPEC</text>
<!-- electric discharge from coin -->
<polyline points="108,72 120,65 118,58" stroke="#fbbf24" stroke-width="2.5" fill="none" filter="url(#elecGlow)" class="spark1">
  <animate attributeName="opacity" values="1;0.3;1" dur="0.4s" repeatCount="indefinite"/>
</polyline>
<polyline points="108,78 122,85 120,92" stroke="#fbbf24" stroke-width="2" fill="none" filter="url(#elecGlow)" class="spark2">
  <animate attributeName="opacity" values="0.3;1;0.3" dur="0.5s" repeatCount="indefinite"/>
</polyline>
<polyline points="52,68 38,62 40,55" stroke="#c4b5fd" stroke-width="1.8" fill="none" filter="url(#elecGlow)" class="spark3">
  <animate attributeName="opacity" values="0.5;1;0.5" dur="0.6s" repeatCount="indefinite"/>
</polyline>
<polyline points="55,80 40,88 42,95" stroke="#c4b5fd" stroke-width="1.5" fill="none" filter="url(#elecGlow)" class="spark1">
  <animate attributeName="opacity" values="1;0.4;1" dur="0.35s" repeatCount="indefinite"/>
</polyline>
<!-- small sparks -->
<circle cx="125" cy="55" r="2" fill="#fbbf24" filter="url(#elecGlow)" class="spark2">
  <animate attributeName="r" values="2;0.5;2" dur="0.5s" repeatCount="indefinite"/>
</circle>
<circle cx="35" cy="95" r="1.5" fill="#c4b5fd" filter="url(#elecGlow)" class="spark3">
  <animate attributeName="r" values="0.5;2;0.5" dur="0.4s" repeatCount="indefinite"/>
</circle>
<!-- Level badge -->
<rect x="55" y="110" width="50" height="18" rx="9" fill="#7c3aed"/>
<text x="80" y="123" font-size="11" fill="#fbbf24" text-anchor="middle" font-weight="800" letter-spacing="1">Lv.2</text>
<!-- tagline -->
<text x="80" y="145" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="600" letter-spacing="2">RAILGUN</text>
</svg>"""

    return f"""<svg width="160" height="160" viewBox="0 0 160 160" class="{cls}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="rcoinGrad" cx="35%" cy="30%" r="65%">
    <stop offset="0%" stop-color="#fde68a"/>
    <stop offset="40%" stop-color="#f59e0b"/>
    <stop offset="100%" stop-color="#d97706"/>
  </radialGradient>
  <filter id="rcoinGlow">
    <feGaussianBlur stdDeviation="1" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- background ring — dimmed -->
<circle cx="80" cy="80" r="70" fill="none" stroke="#7c3aed" stroke-width="1" opacity="0.08"/>
<!-- THE COIN — lying flat on surface, not spinning -->
<ellipse cx="80" cy="85" rx="30" ry="12" fill="#d97706" opacity="0.3"/>
<ellipse cx="80" cy="80" rx="30" ry="30" fill="url(#rcoinGrad)" filter="url(#rcoinGlow)" opacity="0.9"/>
<ellipse cx="80" cy="80" rx="22" ry="22" fill="none" stroke="#d97706" stroke-width="1" opacity="0.4"/>
<!-- coin detail -->
<text x="80" y="88" font-size="24" fill="#92400e" text-anchor="middle" font-weight="900" font-family="serif" opacity="0.5">¥</text>
<text x="80" y="76" font-size="6" fill="#d97706" text-anchor="middle" font-weight="700" letter-spacing="4" opacity="0.4">SPEC</text>
<!-- faint residual spark -->
<circle cx="105" cy="65" r="1.5" fill="#fbbf24" opacity="0.3" class="spark1">
  <animate attributeName="opacity" values="0.3;0.1;0.3" dur="2s" repeatCount="indefinite"/>
</circle>
<circle cx="55" cy="70" r="1" fill="#c4b5fd" opacity="0.2" class="spark2">
  <animate attributeName="opacity" values="0.2;0.05;0.2" dur="3s" repeatCount="indefinite"/>
</circle>
<!-- zzz floating -->
<text x="115" y="55" font-size="16" fill="#a5b4fc" class="float-z" font-weight="700">z</text>
<text x="128" y="43" font-size="13" fill="#a5b4fc" class="float-z2" font-weight="700">z</text>
<text x="138" y="34" font-size="10" fill="#a5b4fc" class="float-z3" font-weight="700">z</text>
<!-- Level badge — dimmed -->
<rect x="55" y="118" width="50" height="16" rx="8" fill="#7c3aed" opacity="0.6"/>
<text x="80" y="130" font-size="10" fill="#fbbf24" text-anchor="middle" font-weight="800" letter-spacing="1" opacity="0.7">Lv.2</text>
</svg>"""


_SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def _sparkline_html(rates: list[float]) -> str:
    """Render rolling success rates as an ASCII sparkline with trend coloring.

    Takes the last 20 data points. Maps values linearly to Unicode block chars.
    Wraps each char in a <span> with class="trend-down" if rate is lower than predecessor.
    Returns HTML string for the sparkline card.
    """
    if not rates:
        return '<div class="value">—</div>'

    recent = rates[-20:]

    if all(r == recent[0] for r in recent):
        char = "▄"
        spans = []
        for i, _ in enumerate(recent):
            cls = ' class="trend-down"' if (i > 0 and recent[i] < recent[i - 1]) else ""
            spans.append(f"<span{cls}>{char}</span>")
        return f'<div class="value" style="font-size:1.2rem;letter-spacing:2px">{"".join(spans)}</div>'

    min_val = min(recent)
    max_val = max(recent)
    val_range = max_val - min_val

    spans = []
    for i, r in enumerate(recent):
        if val_range == 0:
            idx = 3
        else:
            idx = min(int((r - min_val) / val_range * 7), 7)
        char = _SPARKLINE_CHARS[idx]
        cls = ' class="trend-down"' if (i > 0 and recent[i] < recent[i - 1]) else ""
        spans.append(f"<span{cls}>{char}</span>")

    return f'<div class="value" style="font-size:1.2rem;letter-spacing:2px">{"".join(spans)}</div>'


def _rate_class(pct: float) -> str:
    if pct >= 80:
        return "good"
    if pct >= 50:
        return "warn"
    return "bad"


def _phase_table(phase_stats: dict) -> str:
    if not phase_stats:
        return '<div class="meta">No phase data yet</div>'
    rows = ""
    for phase, s in phase_stats.items():
        if s.get("count", 0) == 0:
            continue
        pr = s.get("pass_rate", 0)
        pt = s.get("total_prompt_tokens", 0)
        ct = s.get("total_completion_tokens", 0)
        rows += f"""<tr>
  <td>{phase}</td>
  <td>{s['count']}</td>
  <td class="{_rate_class(pr)}">{pr}%</td>
  <td>{s.get('avg_turns', '—')}</td>
  <td>{s.get('avg_seconds', '—')}s</td>
  <td>{s.get('total_fixes', 0)}</td>
  <td>{s.get('total_llm_calls', 0)}</td>
  <td>{s.get('total_tool_calls', 0)}</td>
  <td>{_fmt_tokens(pt + ct)}</td>
</tr>"""
    return f"""<table>
<thead><tr><th>Phase</th><th>Count</th><th>Pass Rate</th><th>Avg Turns</th><th>Avg Time</th><th>Fixes</th><th>LLM Calls</th><th>Tool Calls</th><th>Tokens</th></tr></thead>
<tbody>{rows}</tbody></table>"""


def _milestone_card(m: dict) -> str:
    from .db import load_level_snapshot
    color = m.get("color", "#8b5cf6")
    icon = m.get("icon", "⚡")
    level_tag = m.get("level_tag", "")

    level_snap = load_level_snapshot(level_tag) if level_tag else None

    if level_snap:
        status = f"{icon} ACHIEVED"
        snap_time = level_snap.get("_level_achieved_at", "")[:16]
        status += f'<span style="font-size:0.7rem;color:#64748b;margin-left:0.5rem">@ {snap_time}</span>'
    else:
        status = "🚧 Leveling Up"

    desc = m.get("description", "")
    desc_html = f'<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:0.6rem">{desc}</div>' if desc else ''

    criteria_html = ""
    for c in m["criteria"]:
        if level_snap:
            c_icon = "✓"
            fill_color = color
            display_current = c["threshold"]
            display_pct = 100
        else:
            c_icon = "✓" if c["met"] else "○"
            fill_color = color if c["met"] else "#475569"
            display_current = c["current"]
            display_pct = c["progress_pct"]
        criteria_html += f"""<div class="criterion">
  <span class="icon">{c_icon}</span>
  <span>{c['description']}</span>
  <div class="progress"><div class="fill" style="width:{display_pct}%;background:{fill_color}"></div></div>
  <span style="color:#94a3b8;font-size:0.8rem">{display_current}/{c['threshold']}</span>
</div>"""

    tasks_html = ""
    tasks = m.get("tasks", [])
    if tasks:
        tasks_completed = m.get("tasks_completed", 0)
        tasks_total = m.get("tasks_total", len(tasks))
        tasks_html = f'<div style="margin-top:0.8rem;font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Capability Tasks ({tasks_completed}/{tasks_total})</div>'
        for t in tasks:
            if level_snap:
                t_icon = "✅"
                t_style = "color:#94a3b8;"
                bar_color = color
                t_pct = 100
                t_found = t["total"]
            else:
                t_icon = "✅" if t["done"] else "⬜"
                t_style = "color:#94a3b8;" if t["done"] else "color:#64748b;"
                bar_color = color if t["done"] else "#334155"
                t_pct = t["progress_pct"]
                t_found = t["found"]
            tasks_html += f"""<div class="criterion">
  <span class="icon">{t_icon}</span>
  <span style="{t_style}" title="{t.get('acceptance', '')}">{t['title']}</span>
  <div class="progress"><div class="fill" style="width:{t_pct}%;background:{bar_color}"></div></div>
  <span style="color:#64748b;font-size:0.75rem">{t_found}/{t['total']}</span>
</div>"""

    return f"""<div class="milestone" style="border-color:{color}">
  <h3 style="color:{color}">{icon} {m['label']} — {status}</h3>
  {desc_html}
  {criteria_html}
  {tasks_html}
</div>"""


def _current_level(milestones: list[dict]) -> str:
    achieved = []
    for m in milestones:
        if m["all_met"]:
            achieved.append(m)
    if not achieved:
        return "⚡ Pre-L2 · 超电磁开发智能体"
    top = achieved[-1]
    return f"{top['icon']} {top['label']} · 超电磁开发智能体"


def _recent_list(names: list[str]) -> str:
    if not names:
        return '<li class="meta">No changes yet</li>'
    return "\n".join(f"<li>{n}</li>" for n in names)


def _fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    if s < 3600:
        return f"{s/60:.1f}min"
    h = s / 3600
    return f"{h:.1f}h"


def _fmt_tokens(n: int) -> str:
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n/1000:.1f}K"
    return f"{n/1_000_000:.2f}M"


def _usage_section(stats: dict) -> str:
    llm = stats.get("total_llm_calls", 0)
    tool = stats.get("total_tool_calls", 0)
    runtime = stats.get("total_runtime_seconds", 0)
    changes = stats.get("total_changes", 0)
    avg_llm = round(llm / changes, 1) if changes else 0
    avg_tool = round(tool / changes, 1) if changes else 0
    prompt_tokens = stats.get("total_prompt_tokens", 0)
    completion_tokens = stats.get("total_completion_tokens", 0)
    total_tokens = prompt_tokens + completion_tokens
    avg_tokens = round(total_tokens / changes) if changes else 0

    return f"""<div class="section">
    <h2>⚡ Resource Usage</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Total Tokens</div>
      <div class="value">{_fmt_tokens(total_tokens)}</div>
      <div class="meta">{_fmt_tokens(prompt_tokens)} prompt + {_fmt_tokens(completion_tokens)} completion</div>
    </div>
    <div class="card">
      <div class="label">Avg Tokens / Change</div>
      <div class="value">{_fmt_tokens(avg_tokens)}</div>
    </div>
    <div class="card">
      <div class="label">Total LLM Calls</div>
      <div class="value">{llm:,}</div>
      <div class="meta">avg {avg_llm} per change</div>
    </div>
    <div class="card">
      <div class="label">Total Tool Calls</div>
      <div class="value">{tool:,}</div>
      <div class="meta">avg {avg_tool} per change</div>
    </div>
    <div class="card">
      <div class="label">Total Runtime</div>
      <div class="value">{_fmt_seconds(runtime)}</div>
      <div class="meta">{runtime:,.0f}s total</div>
    </div>
  </div>
</div>"""


_MOOD_STYLE = {
    "praise": ("#22c55e", "💛"),
    "criticism": ("#f59e0b", "📝"),
    "milestone": ("#a78bfa", "🏆"),
    "learned": ("#38bdf8", "💡"),
    "note": ("#94a3b8", "📝"),
}


def _journal_section() -> str:
    entries = load_journal()
    if not entries:
        return ""
    rows = ""
    for e in reversed(entries):
        color, icon = _MOOD_STYLE.get(e.get("mood", "note"), _MOOD_STYLE["note"])
        ts = e.get("ts", "")[:16].replace("T", " ")
        author = e.get("author", "")
        text = e["text"].replace("<", "&lt;").replace(">", "&gt;")
        rows += f"""<div class="journal-entry" style="border-left:3px solid {color}">
  <div class="journal-header">
    <span>{icon}</span>
    <span class="journal-text">{text}</span>
  </div>
  <div class="journal-meta">{ts} · {author}</div>
</div>\n"""
    return f"""<div class="section">
  <h2>💭 Growth Journal</h2>
  <div class="journal">
    {rows}
  </div>
</div>"""


_TODO_STATUS_ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⬜",
    "cancelled": "🚫",
    "blocked": "🔒",
}


def _load_todos(base_path: str = None) -> list[dict]:
    """Scan data/todos/*.json, sort by mtime (newest first), return top 5."""
    if base_path is None:
        base_path = str(Path(__file__).resolve().parent.parent.parent)
    todos_dir = Path(base_path) / "data" / "todos"
    if not todos_dir.exists():
        return []
    files = list(todos_dir.glob("*.json"))
    if not files:
        return []
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    files = files[:5]
    results = []
    for fpath in files:
        raw = fpath.read_text(encoding="utf-8").strip()
        if not raw:
            continue
        try:
            items = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(items, list):
            continue
        name = fpath.stem
        total = len(items)
        completed = sum(1 for it in items if it.get("status") == "completed")
        pct = round(completed / total * 100) if total else 0
        results.append({
            "name": name,
            "summary": f"{completed}/{total} completed ({pct}%)",
            "pct": pct,
            "items": items,
        })
    return results


def _todo_section(base_path: str = None) -> str:
    """Render todo progress cards. Returns empty string if no todos."""
    todos = _load_todos(base_path)
    if not todos:
        return ""
    cards = ""
    for td in todos:
        items_html = ""
        for it in td["items"]:
            status = it.get("status", "pending")
            icon = _TODO_STATUS_ICONS.get(status, "⬜")
            content = it.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
            items_html += f"""<div class="criterion">
  <span class="icon">{icon}</span>
  <span>{content}</span>
</div>
"""
        color = "#22c55e" if td["pct"] == 100 else "#7c3aed"
        fill_bg = "#22c55e" if td["pct"] == 100 else "#7c3aed"
        cards += f"""<div class="milestone" style="border-color:{color}">
  <h3 style="color:{color}">📋 {td['name']} — {td['summary']}</h3>
  {items_html}
  <div class="criterion">
    <div class="progress"><div class="fill" style="width:{td['pct']}%;background:{fill_bg}"></div></div>
    <span style="color:#94a3b8;font-size:0.8rem">{td['pct']}%</span>
  </div>
</div>
"""
    return f"""<div class="section">
  <h2>📋 Todo Progress</h2>
  {cards}
</div>"""
