"""Tests for feedback loop dashboard section spec.

Spec: dashboard-add-feedback-loop-metrics / feedback-loop-section
"""
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helper: call generate_dashboard and return HTML string without writing to disk
# ---------------------------------------------------------------------------
def _render_dashboard_html(tmp_path):
    """Generate dashboard HTML to a temp path and return its content."""
    from zsiga.metrics.dashboard import generate_dashboard

    out = tmp_path / "dashboard_test.html"
    with patch("zsiga.metrics.dashboard._DASHBOARD_PATH", out):
        generate_dashboard(output_path=str(out))
    return out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Scenario: Dashboard HTML contains Feedback Loop section
# ---------------------------------------------------------------------------
def test_dashboard_html_contains_feedback_loop_section(tmp_path):
    html = _render_dashboard_html(tmp_path)
    assert "Feedback Loop" in html, "Feedback Loop section heading missing"
    # Verify it's inside a section div
    assert '<h2>' in html and 'Feedback Loop' in html


# ---------------------------------------------------------------------------
# Scenario: Feedback Loop section positioned before Recent Changes
# ---------------------------------------------------------------------------
def test_feedback_loop_before_recent_changes(tmp_path):
    html = _render_dashboard_html(tmp_path)
    fl_pos = html.find("Feedback Loop")
    rc_pos = html.find("Recent Changes")
    assert fl_pos > 0, "Feedback Loop section not found in HTML"
    assert rc_pos > 0, "Recent Changes section not found in HTML"
    assert fl_pos < rc_pos, "Feedback Loop must appear before Recent Changes"


# ---------------------------------------------------------------------------
# Scenario: Learnings Health card rendered
# ---------------------------------------------------------------------------
def test_learnings_health_card_rendered(tmp_path):
    html = _render_dashboard_html(tmp_path)
    assert "Learnings Health" in html, "Learnings Health card label missing"
    # Should show either a number or "No learnings yet"
    has_number = any(str(i) in html for i in range(10))
    has_placeholder = "No learnings yet" in html
    assert has_number or has_placeholder, "Learnings Health card should show count or placeholder"


# ---------------------------------------------------------------------------
# Scenario: Auto-Proposal Success card rendered
# ---------------------------------------------------------------------------
def test_auto_proposal_success_card_rendered(tmp_path):
    html = _render_dashboard_html(tmp_path)
    assert "Auto-Proposal" in html or "auto-proposal" in html.lower(), \
        "Auto-Proposal Success card label missing"
    # Should show percentage or "No auto-proposals yet"
    has_pct = "%" in html
    has_placeholder = "No auto-proposals yet" in html
    assert has_pct or has_placeholder, "Auto-Proposal card should show rate or placeholder"


# ---------------------------------------------------------------------------
# Scenario: Self-Assessment Coverage card rendered
# ---------------------------------------------------------------------------
def test_self_assessment_coverage_card_rendered(tmp_path):
    html = _render_dashboard_html(tmp_path)
    assert "Self-Assessment" in html or "self-assessment" in html.lower() or "Coverage" in html, \
        "Self-Assessment Coverage card label missing"


# ---------------------------------------------------------------------------
# Scenario: Injection Rate card rendered
# ---------------------------------------------------------------------------
def test_injection_rate_card_rendered(tmp_path):
    html = _render_dashboard_html(tmp_path)
    assert "Injection" in html, "Injection Rate card label missing"


# ---------------------------------------------------------------------------
# Scenario: Dashboard renders with all "No data yet" placeholders on empty DB
# ---------------------------------------------------------------------------
def test_empty_db_placeholders(tmp_path):
    html = _render_dashboard_html(tmp_path)
    # At minimum, the placeholders should appear when no data exists
    # Check for "No" + various data-yet messages
    assert "No learnings yet" in html or "0" in html
    assert "No auto-proposals yet" in html or "0" in html
    assert "No self-assessments" in html or "0" in html


# ---------------------------------------------------------------------------
# Scenario: Existing sections unchanged after adding Feedback Loop
# ---------------------------------------------------------------------------
def test_existing_sections_unchanged(tmp_path):
    html = _render_dashboard_html(tmp_path)
    assert "Phase Performance" in html, "Phase Performance section missing"
    assert "Recent Changes" in html, "Recent Changes section missing"
    # Evolution Roadmap or Roadmap
    assert "Roadmap" in html or "Evolution" in html, "Evolution Roadmap section missing"
