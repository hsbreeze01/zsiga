from pathlib import Path
from .collector import load_all_changes, compute_stats, check_milestone
from .types import MILESTONE_L2, MILESTONE_L3

_DASHBOARD_PATH = Path(__file__).resolve().parent.parent.parent / "site" / "dashboard.html"


def generate_dashboard(output_path: str = None) -> str:
    stats = compute_stats()
    l2 = check_milestone(stats, MILESTONE_L2)
    l3 = check_milestone(stats, MILESTONE_L3)
    html = _render(stats, l2, l3)

    out = Path(output_path) if output_path else _DASHBOARD_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)


def _render(stats: dict, l2: dict, l3: dict) -> str:
    phase_rows = _phase_table(stats.get("phase_stats", {}))
    l2_card = _milestone_card(l2, "#f59e0b")
    l3_card = _milestone_card(l3, "#8b5cf6")
    recent = _recent_list(stats.get("recent_changes", []))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
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
</style>
</head>
<body>
<h1>zsiga <span>autonomous development agent</span></h1>

<div class="grid">
  <div class="card">
    <div class="label">Total Changes</div>
    <div class="value">{stats['total_changes']}</div>
  </div>
  <div class="card">
    <div class="label">Success Rate</div>
    <div class="value {_rate_class(stats['success_rate_pct'])}">{stats['success_rate_pct']}%</div>
    <div class="meta">{stats['successful_changes']} ok / {stats['failed_changes']} fail</div>
  </div>
  <div class="card">
    <div class="label">Projects</div>
    <div class="value">{stats['distinct_projects']}</div>
    <div class="meta">{', '.join(stats['projects']) if stats['projects'] else '—'}</div>
  </div>
  <div class="card">
    <div class="label">Lessons</div>
    <div class="value">{stats['lessons_learned']}</div>
  </div>
  <div class="card">
    <div class="label">First-Pass Test Rate</div>
    <div class="value {_rate_class(stats['first_pass_test_rate_pct'])}">{stats['first_pass_test_rate_pct']}%</div>
  </div>
  <div class="card">
    <div class="label">Verify Pass Rate</div>
    <div class="value {_rate_class(stats['verify_pass_rate_pct'])}">{stats['verify_pass_rate_pct']}%</div>
  </div>
</div>

<div class="section">
  <h2>Phase Performance</h2>
  {phase_rows}
</div>

<div class="section">
  <h2>Milestones</h2>
  {l2_card}
  {l3_card}
</div>

<div class="section">
  <h2>Recent Changes</h2>
  <ul class="recent">
    {recent}
  </ul>
</div>

<div class="meta" style="margin-top:2rem">Updated: {stats['last_updated']}</div>
</body>
</html>"""


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
        rows += f"""<tr>
  <td>{phase}</td>
  <td>{s['count']}</td>
  <td class="{_rate_class(pr)}">{pr}%</td>
  <td>{s.get('avg_turns', '—')}</td>
  <td>{s.get('avg_seconds', '—')}s</td>
  <td>{s.get('total_fixes', 0)}</td>
</tr>"""
    return f"""<table>
<thead><tr><th>Phase</th><th>Count</th><th>Pass Rate</th><th>Avg Turns</th><th>Avg Time</th><th>Fixes</th></tr></thead>
<tbody>{rows}</tbody></table>"""


def _milestone_card(m: dict, color: str) -> str:
    status = "✅ READY" if m["all_met"] else "🚧 In Progress"
    criteria = ""
    for c in m["criteria"]:
        icon = "✓" if c["met"] else "○"
        fill_color = color if c["met"] else "#475569"
        criteria += f"""<div class="criterion">
  <span class="icon">{icon}</span>
  <span>{c['description']}</span>
  <div class="progress"><div class="fill" style="width:{c['progress_pct']}%;background:{fill_color}"></div></div>
  <span style="color:#94a3b8;font-size:0.8rem">{c['current']}/{c['threshold']}</span>
</div>"""
    return f"""<div class="milestone" style="border-color:{color}">
  <h3>{m['label']} — {status}</h3>
  {criteria}
</div>"""


def _recent_list(names: list[str]) -> str:
    if not names:
        return '<li class="meta">No changes yet</li>'
    return "\n".join(f"<li>{n}</li>" for n in names)
