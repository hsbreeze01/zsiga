from datetime import datetime
from pathlib import Path
from .collector import load_all_changes, compute_stats, check_milestone
from .types import MILESTONE_L2, MILESTONE_L3

_DASHBOARD_PATH = Path(__file__).resolve().parent.parent.parent / "site" / "dashboard.html"


def _detect_state(stats: dict) -> str:
    ts = stats.get("last_updated", "")
    if not ts:
        return "resting"
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
        return "working" if elapsed < 3600 else "resting"
    except (ValueError, TypeError):
        return "resting"


def generate_dashboard(output_path: str = None) -> str:
    stats = compute_stats()
    l2 = check_milestone(stats, MILESTONE_L2)
    l3 = check_milestone(stats, MILESTONE_L3)
    state = _detect_state(stats)
    html = _render(stats, l2, l3, state)

    out = Path(output_path) if output_path else _DASHBOARD_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)


def _render(stats: dict, l2: dict, l3: dict, state: str = "resting") -> str:
    phase_rows = _phase_table(stats.get("phase_stats", {}))
    l2_card = _milestone_card(l2, "#f59e0b")
    l3_card = _milestone_card(l3, "#8b5cf6")
    recent = _recent_list(stats.get("recent_changes", []))
    usage_section = _usage_section(stats)
    mascot = _mascot_svg(state)

    state_label = "🛠️ Working" if state == "working" else "💤 Resting"

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
</style>
</head>
<body>

<div class="hero">
  <div class="hero-mascot">
    {mascot}
  </div>
  <div class="hero-info">
    <h1>zsiga <span>autonomous development agent</span></h1>
    <span class="state-badge {state}">{state_label}</span>
  </div>
</div>

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

{usage_section}

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


def _mascot_svg(state: str = "resting") -> str:
    cls = "mascot-working" if state == "working" else "mascot-resting"
    if state == "working":
        return f"""<svg width="140" height="170" viewBox="0 0 140 170" class="{cls}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="wBody" cx="40%" cy="35%" r="60%">
    <stop offset="0%" stop-color="#c4b5fd"/>
    <stop offset="100%" stop-color="#7c3aed"/>
  </radialGradient>
  <radialGradient id="wCheek" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fda4af"/>
    <stop offset="100%" stop-color="#fb7185"/>
  </radialGradient>
  <radialGradient id="wScreen" cx="50%" cy="30%" r="70%">
    <stop offset="0%" stop-color="#1e293b"/>
    <stop offset="100%" stop-color="#0f172a"/>
  </radialGradient>
  <linearGradient id="wHat" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#fbbf24"/>
    <stop offset="100%" stop-color="#f59e0b"/>
  </linearGradient>
</defs>
<!-- shadow -->
<ellipse cx="70" cy="163" rx="30" ry="5" fill="#7c3aed30"/>
<!-- body -->
<rect x="48" y="105" width="44" height="38" rx="16" fill="url(#wBody)"/>
<!-- feet -->
<ellipse cx="55" cy="146" rx="12" ry="7" fill="#7c3aed"/>
<ellipse cx="85" cy="146" rx="12" ry="7" fill="#7c3aed"/>
<!-- laptop base -->
<rect x="30" y="130" width="50" height="5" rx="2" fill="#475569"/>
<rect x="35" y="125" width="40" height="8" rx="2" fill="#334155"/>
<!-- laptop screen -->
<rect x="35" y="100" width="40" height="28" rx="3" fill="url(#wScreen)"/>
<!-- code lines on screen -->
<rect x="40" y="106" width="18" height="2.5" rx="1" fill="#34d399" class="spark1"/>
<rect x="40" y="111" width="24" height="2.5" rx="1" fill="#38bdf8" class="spark2"/>
<rect x="40" y="116" width="14" height="2.5" rx="1" fill="#fbbf24" class="spark3"/>
<rect x="40" y="121" width="20" height="2.5" rx="1" fill="#818cf8" class="spark1"/>
<!-- head -->
<circle cx="70" cy="60" r="42" fill="url(#wBody)"/>
<!-- hard hat -->
<ellipse cx="70" cy="24" rx="35" ry="10" fill="url(#wHat)"/>
<rect x="42" y="24" width="56" height="14" rx="4" fill="url(#wHat)"/>
<rect x="60" y="16" width="20" height="12" rx="4" fill="#fbbf24"/>
<!-- eyes - wide open, determined -->
<ellipse cx="55" cy="58" rx="9" ry="10" fill="white"/>
<ellipse cx="85" cy="58" rx="9" ry="10" fill="white"/>
<circle cx="57" cy="59" r="5.5" fill="#1e1b4b"/>
<circle cx="87" cy="59" r="5.5" fill="#1e1b4b"/>
<!-- eye highlights -->
<circle cx="59" cy="56" r="2" fill="white"/>
<circle cx="89" cy="56" r="2" fill="white"/>
<!-- cheeks -->
<circle cx="42" cy="70" r="6" fill="url(#wCheek)" opacity="0.5"/>
<circle cx="98" cy="70" r="6" fill="url(#wCheek)" opacity="0.5"/>
<!-- mouth - excited "o" -->
<ellipse cx="70" cy="76" rx="5" ry="4" fill="#4c1d95"/>
<!-- arms reaching to keyboard -->
<rect x="30" y="112" width="12" height="6" rx="3" fill="#a78bfa"/>
<rect x="98" y="112" width="12" height="6" rx="3" fill="#a78bfa"/>
<!-- sparkles -->
<text x="18" y="45" font-size="12" class="spark1">✦</text>
<text x="112" y="40" font-size="10" class="spark2">✦</text>
<text x="105" y="95" font-size="8" class="spark3">✦</text>
<text x="22" y="90" font-size="9" class="spark2">✧</text>
</svg>"""

    return f"""<svg width="140" height="170" viewBox="0 0 140 170" class="{cls}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="rBody" cx="40%" cy="35%" r="60%">
    <stop offset="0%" stop-color="#c4b5fd"/>
    <stop offset="100%" stop-color="#7c3aed"/>
  </radialGradient>
  <radialGradient id="rCheek" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fda4af"/>
    <stop offset="100%" stop-color="#fb7185"/>
  </radialGradient>
  <radialGradient id="rCushion" cx="50%" cy="60%" r="60%">
    <stop offset="0%" stop-color="#a5b4fc"/>
    <stop offset="100%" stop-color="#6366f1"/>
  </radialGradient>
</defs>
<!-- shadow -->
<ellipse cx="70" cy="158" rx="35" ry="6" fill="#6366f120"/>
<!-- cushion -->
<ellipse cx="70" cy="148" rx="38" ry="14" fill="url(#rCushion)"/>
<ellipse cx="70" cy="145" rx="32" ry="8" fill="#818cf880"/>
<!-- body - sitting relaxed -->
<rect x="45" y="105" width="50" height="40" rx="18" fill="url(#rBody)"/>
<!-- feet dangled -->
<ellipse cx="52" cy="142" rx="10" ry="6" fill="#7c3aed"/>
<ellipse cx="88" cy="142" rx="10" ry="6" fill="#7c3aed"/>
<!-- head -->
<circle cx="70" cy="60" r="42" fill="url(#rBody)"/>
<!-- sleeping cap -->
<path d="M40,38 Q50,8 70,18 Q90,8 100,38" fill="#818cf8"/>
<circle cx="70" cy="14" r="6" fill="#c4b5fd"/>
<!-- eyes - happy closed arcs -->
<path d="M47,58 Q55,52 63,58" stroke="#1e1b4b" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path d="M77,58 Q85,52 93,58" stroke="#1e1b4b" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<!-- cheeks -->
<circle cx="42" cy="70" r="6" fill="url(#rCheek)" opacity="0.5"/>
<circle cx="98" cy="70" r="6" fill="url(#rCheek)" opacity="0.5"/>
<!-- mouth - content smile -->
<path d="M63,76 Q70,82 77,76" stroke="#4c1d95" stroke-width="2" fill="none" stroke-linecap="round"/>
<!-- arms resting on belly -->
<ellipse cx="42" cy="118" rx="10" ry="6" fill="#a78bfa"/>
<ellipse cx="98" cy="118" rx="10" ry="6" fill="#a78bfa"/>
<!-- zzz floating -->
<text x="108" y="38" font-size="14" fill="#a5b4fc" class="float-z" font-weight="700">z</text>
<text x="118" y="28" font-size="11" fill="#a5b4fc" class="float-z2" font-weight="700">z</text>
<text x="126" y="20" font-size="9" fill="#a5b4fc" class="float-z3" font-weight="700">z</text>
</svg>"""


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
  <td>{s.get('total_llm_calls', 0)}</td>
  <td>{s.get('total_tool_calls', 0)}</td>
</tr>"""
    return f"""<table>
<thead><tr><th>Phase</th><th>Count</th><th>Pass Rate</th><th>Avg Turns</th><th>Avg Time</th><th>Fixes</th><th>LLM Calls</th><th>Tool Calls</th></tr></thead>
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


def _fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    if s < 3600:
        return f"{s/60:.1f}min"
    h = s / 3600
    return f"{h:.1f}h"


def _usage_section(stats: dict) -> str:
    llm = stats.get("total_llm_calls", 0)
    tool = stats.get("total_tool_calls", 0)
    runtime = stats.get("total_runtime_seconds", 0)
    changes = stats.get("total_changes", 0)
    avg_llm = round(llm / changes, 1) if changes else 0
    avg_tool = round(tool / changes, 1) if changes else 0

    return f"""<div class="section">
  <h2>Resource Usage</h2>
  <div class="grid">
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
