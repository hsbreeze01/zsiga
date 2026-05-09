from datetime import datetime
from pathlib import Path
from .collector import load_all_changes, compute_stats, check_milestone
from .types import MILESTONE_L2, MILESTONE_L3
from ..memory.journal import load_journal

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
    journal = _journal_section()
    mascot = _mascot_svg(state)

    state_label = "⚡ Working" if state == "working" else "💤 Resting"

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
.journal {{ display: flex; flex-direction: column; gap: 0.6rem; }}
.journal-entry {{ background: #1e293b; border-radius: 6px; padding: 0.7rem 1rem; }}
.journal-header {{ display: flex; align-items: flex-start; gap: 0.5rem; font-size: 0.88rem; line-height: 1.5; }}
.journal-text {{ flex: 1; }}
.journal-meta {{ font-size: 0.72rem; color: #64748b; margin-top: 0.25rem; }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-mascot">
    {mascot}
  </div>
  <div class="hero-info">
    <h1>zsiga <span>⚡ Level 2 · Code Architect · 超电磁开发智能体</span></h1>
    <span class="state-badge {state}">{state_label}</span>
  </div>
</div>

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

<div class="section">
    <h2>⚡ Phase Performance</h2>
  {phase_rows}
</div>

{usage_section}

<div class="section">
    <h2>🪙 Milestones</h2>
  {l2_card}
  {l3_card}
</div>

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


def _mascot_svg(state: str = "resting") -> str:
    cls = "mascot-working" if state == "working" else "mascot-resting"
    if state == "working":
        return f"""<svg width="160" height="180" viewBox="0 0 160 180" class="{cls}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="hair" cx="45%" cy="30%" r="65%">
    <stop offset="0%" stop-color="#a78bfa"/>
    <stop offset="100%" stop-color="#5b21b6"/>
  </radialGradient>
  <radialGradient id="face" cx="50%" cy="40%" r="50%">
    <stop offset="0%" stop-color="#fef3c7"/>
    <stop offset="100%" stop-color="#fde68a"/>
  </radialGradient>
  <radialGradient id="coin" cx="40%" cy="35%" r="50%">
    <stop offset="0%" stop-color="#fde68a"/>
    <stop offset="50%" stop-color="#f59e0b"/>
    <stop offset="100%" stop-color="#d97706"/>
  </radialGradient>
  <radialGradient id="boltGrad" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fbbf24"/>
    <stop offset="100%" stop-color="#7c3aed"/>
  </radialGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- shadow -->
<ellipse cx="80" cy="172" rx="35" ry="5" fill="#7c3aed20"/>
<!-- hair back -->
<ellipse cx="80" cy="55" rx="48" ry="50" fill="url(#hair)"/>
<!-- hair strands flowing right (signature Misaka style) -->
<path d="M100,25 Q120,18 118,40 Q122,30 130,38 Q125,22 115,15" fill="url(#hair)" opacity="0.9"/>
<path d="M105,30 Q125,28 128,48 Q130,35 135,45 Q130,25 118,20" fill="url(#hair)" opacity="0.7"/>
<path d="M95,20 Q110,10 112,28 Q116,16 122,24" fill="url(#hair)" opacity="0.6"/>
<!-- face -->
<ellipse cx="80" cy="62" rx="36" ry="38" fill="url(#face)"/>
<!-- hair bangs -->
<path d="M44,45 Q50,25 65,35 Q55,20 70,22 Q62,15 78,18 Q75,25 82,30 Q72,22 68,35 Q60,28 50,40Z" fill="url(#hair)"/>
<!-- hair clip (Gekota frog pin) -->
<circle cx="55" cy="32" r="4" fill="#22c55e"/>
<circle cx="55" cy="32" r="2" fill="#16a34a"/>
<!-- eyes - determined, sharp -->
<ellipse cx="66" cy="60" rx="10" ry="11" fill="white"/>
<ellipse cx="94" cy="60" rx="10" ry="11" fill="white"/>
<circle cx="68" cy="61" r="6.5" fill="#7c3aed"/>
<circle cx="96" cy="61" r="6.5" fill="#7c3aed"/>
<circle cx="67" cy="59" r="2.5" fill="white"/>
<circle cx="95" cy="59" r="2.5" fill="white"/>
<!-- eyebrows - determined -->
<path d="M56,48 Q66,43 76,47" stroke="#5b21b6" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path d="M84,47 Q94,43 104,48" stroke="#5b21b6" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<!-- cheeks - slight blush -->
<circle cx="52" cy="72" r="5" fill="#fda4af" opacity="0.4"/>
<circle cx="108" cy="72" r="5" fill="#fda4af" opacity="0.4"/>
<!-- mouth - confident smirk -->
<path d="M74,78 Q80,82 86,78" stroke="#92400e" stroke-width="1.8" fill="none" stroke-linecap="round"/>
<!-- body (Tokiwadai-style uniform, purple) -->
<rect x="58" y="98" width="44" height="35" rx="8" fill="#7c3aed"/>
<rect x="62" y="98" width="36" height="18" rx="4" fill="white"/>
<path d="M68,98 L80,112 L92,98" fill="none" stroke="#7c3aed" stroke-width="2"/>
<!-- skirt -->
<path d="M55,130 Q58,145 52,155 L108,155 Q102,145 105,130 Q80,135 55,130Z" fill="#5b21b6"/>
<!-- legs -->
<rect x="65" y="152" width="8" height="16" rx="4" fill="#fde68a"/>
<rect x="87" y="152" width="8" height="16" rx="4" fill="#fde68a"/>
<!-- shoes -->
<ellipse cx="69" cy="168" rx="8" ry="4" fill="#1e1b4b"/>
<ellipse cx="91" cy="168" rx="8" ry="4" fill="#1e1b4b"/>
<!-- right arm flicking coin -->
<line x1="102" y1="108" x2="130" y2="90" stroke="#7c3aed" stroke-width="8" stroke-linecap="round"/>
<circle cx="130" cy="86" r="3" fill="#fde68a"/>
<!-- THE COIN - spinning mid-air -->
<ellipse cx="138" cy="78" rx="8" ry="4" fill="url(#coin)" filter="url(#glow)" class="spark1">
  <animateTransform attributeName="transform" type="rotate" from="0 138 78" to="360 138 78" dur="0.6s" repeatCount="indefinite"/>
</ellipse>
<!-- coin detail -->
<text x="136" y="81" font-size="6" fill="#92400e" font-weight="bold" text-anchor="middle">¥</text>
<!-- left arm at side -->
<line x1="58" y1="108" x2="42" y2="125" stroke="#7c3aed" stroke-width="8" stroke-linecap="round"/>
<!-- ELECTRIC ARCS -->
<polyline points="132,74 136,68 134,62" stroke="#fbbf24" stroke-width="1.5" fill="none" filter="url(#glow)" class="spark1"/>
<polyline points="140,76 146,70 144,64" stroke="#fbbf24" stroke-width="1.2" fill="none" filter="url(#glow)" class="spark2"/>
<polyline points="136,82 140,88 138,94" stroke="#fbbf24" stroke-width="1" fill="none" filter="url(#glow)" class="spark3"/>
<polyline points="128,80 122,76 124,70" stroke="#c4b5fd" stroke-width="1" fill="none" filter="url(#glow)" class="spark2"/>
<polyline points="144,82 150,86 148,92" stroke="#c4b5fd" stroke-width="0.8" fill="none" filter="url(#glow)" class="spark3"/>
<!-- small sparks around coin -->
<text x="150" y="72" font-size="8" fill="#fbbf24" class="spark1">⚡</text>
<text x="122" y="68" font-size="6" fill="#c4b5fd" class="spark2">⚡</text>
<!-- Level badge -->
<rect x="60" y="140" width="40" height="12" rx="6" fill="#fbbf24" opacity="0.9"/>
<text x="80" y="149" font-size="8" fill="#1e1b4b" text-anchor="middle" font-weight="bold">Lv.2</text>
</svg>"""

    return f"""<svg width="160" height="180" viewBox="0 0 160 180" class="{cls}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="rhair" cx="45%" cy="30%" r="65%">
    <stop offset="0%" stop-color="#a78bfa"/>
    <stop offset="100%" stop-color="#5b21b6"/>
  </radialGradient>
  <radialGradient id="rface" cx="50%" cy="40%" r="50%">
    <stop offset="0%" stop-color="#fef3c7"/>
    <stop offset="100%" stop-color="#fde68a"/>
  </radialGradient>
  <radialGradient id="drink" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fbbf24"/>
    <stop offset="100%" stop-color="#f59e0b"/>
  </radialGradient>
  <filter id="rglow">
    <feGaussianBlur stdDeviation="1.5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- shadow -->
<ellipse cx="80" cy="172" rx="40" ry="5" fill="#7c3aed15"/>
<!-- bench / ground -->
<rect x="30" y="148" width="100" height="6" rx="3" fill="#334155"/>
<!-- hair back -->
<ellipse cx="80" cy="58" rx="48" ry="50" fill="url(#rhair)"/>
<!-- face -->
<ellipse cx="80" cy="65" rx="36" ry="38" fill="url(#rface)"/>
<!-- hair bangs (slightly messy, relaxed) -->
<path d="M44,48 Q52,28 66,38 Q56,22 72,25 Q64,18 80,22 Q76,28 82,34 Q74,26 70,38 Q62,32 52,44Z" fill="url(#rhair)"/>
<!-- hair strands right -->
<path d="M100,30 Q118,25 116,45 Q120,35 126,42" fill="url(#rhair)" opacity="0.6"/>
<!-- hair clip -->
<circle cx="55" cy="35" r="3.5" fill="#22c55e"/>
<circle cx="55" cy="35" r="1.5" fill="#16a34a"/>
<!-- eyes - happy closed arcs (content) -->
<path d="M60,63 Q68,56 76,63" stroke="#5b21b6" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path d="M84,63 Q92,56 100,63" stroke="#5b21b6" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<!-- cheeks -->
<circle cx="52" cy="74" r="5" fill="#fda4af" opacity="0.5"/>
<circle cx="108" cy="74" r="5" fill="#fda4af" opacity="0.5"/>
<!-- mouth - content smile -->
<path d="M73,80 Q80,85 87,80" stroke="#92400e" stroke-width="1.8" fill="none" stroke-linecap="round"/>
<!-- body sitting -->
<rect x="58" y="102" width="44" height="32" rx="8" fill="#7c3aed"/>
<rect x="62" y="102" width="36" height="16" rx="4" fill="white"/>
<path d="M68,102 L80,114 L92,102" fill="none" stroke="#7c3aed" stroke-width="2"/>
<!-- skirt sitting -->
<path d="M55,132 Q50,145 48,148 L112,148 Q110,145 105,132 Q80,137 55,132Z" fill="#5b21b6"/>
<!-- legs crossed sitting -->
<ellipse cx="70" cy="155" rx="12" ry="5" fill="#fde68a"/>
<ellipse cx="90" cy="150" rx="12" ry="5" fill="#fde68a"/>
<!-- shoes -->
<ellipse cx="65" cy="158" rx="7" ry="3.5" fill="#1e1b4b"/>
<ellipse cx="95" cy="153" rx="7" ry="3.5" fill="#1e1b4b"/>
<!-- right arm holding drink -->
<line x1="102" y1="112" x2="118" y2="95" stroke="#7c3aed" stroke-width="7" stroke-linecap="round"/>
<circle cx="118" cy="85" r="3" fill="#fde68a"/>
<!-- drink can -->
<rect x="112" y="72" width="14" height="18" rx="4" fill="url(#drink)"/>
<rect x="114" y="74" width="10" height="3" rx="1" fill="white" opacity="0.3"/>
<text x="119" y="86" font-size="5" fill="#92400e" text-anchor="middle" font-weight="bold">☕</text>
<!-- left arm resting -->
<line x1="58" y1="112" x2="44" y2="128" stroke="#7c3aed" stroke-width="7" stroke-linecap="round"/>
<!-- Level badge on skirt -->
<rect x="64" y="138" width="32" height="10" rx="5" fill="#fbbf24" opacity="0.8"/>
<text x="80" y="146" font-size="7" fill="#1e1b4b" text-anchor="middle" font-weight="bold">Lv.2</text>
<!-- zzz with tiny sparks -->
<text x="128" y="50" font-size="14" fill="#a5b4fc" class="float-z" font-weight="700">z</text>
<text x="138" y="40" font-size="11" fill="#a5b4fc" class="float-z2" font-weight="700">z</text>
<text x="146" y="32" font-size="9" fill="#a5b4fc" class="float-z3" font-weight="700">z</text>
<!-- tiny residual spark on fingertip -->
<circle cx="118" cy="72" r="2" fill="#fbbf24" filter="rglow" class="spark1" opacity="0.5"/>
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


def _milestone_card(m: dict, color: str) -> str:
    status = "⚡ ACHIEVED" if m["all_met"] else "🚧 Leveling Up"
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
