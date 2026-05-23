# Delta Spec: Dashboard Feedback Loop Section Rendering

## ADDED Requirements

### Requirement: Feedback Loop Section in Dashboard HTML

The system SHALL render a "Feedback Loop" section in the dashboard HTML output. The section SHALL:

1. Appear **before** the "Change History" section
2. Use the heading text "Feedback Loop"
3. Contain 4 metric cards with the following titles:
   - "Learnings Health"
   - "Injection Rate"
   - "Auto-Proposal Success"
   - "Self-Assessment Coverage"
4. Each card SHALL display its metric values or "No data yet" when values are zero/null/N/A
5. Use existing `.card` and `.section` CSS classes from the dashboard template
6. Be rendered server-side in Python (no client-side JS required for this section)

#### Scenario: Dashboard HTML contains Feedback Loop section before Change History

- **testable**: true
- **target**: zsiga/dashboard.py::render_feedback_loop_section
- **Given** feedback metrics with at least one non-empty value (e.g., `learnings_health.total == 5`)
- **When** the dashboard HTML is rendered with these metrics
- **Then** the output HTML contains the text `"Feedback Loop"`, the text `"Change History"` appears after the `"Feedback Loop"` text, and the output contains all 4 card titles: `"Learnings Health"`, `"Injection Rate"`, `"Auto-Proposal Success"`, `"Self-Assessment Coverage"`

#### Scenario: Feedback Loop section uses existing CSS classes

- **testable**: true
- **target**: zsiga/dashboard.py::render_feedback_loop_section
- **Given** any valid feedback metrics dict
- **When** the Feedback Loop section HTML is rendered
- **Then** the output contains elements with class `"card"` and an element with class `"section"` wrapping the Feedback Loop content

---

### Requirement: No Data Yet Fallback

When all 4 metric sub-dicts contain only zero/null/N/A default values, each card in the Feedback Loop section SHALL display the text `"No data yet"` instead of numeric values. The section itself SHALL still be rendered (not hidden or omitted).

#### Scenario: Empty metrics produce No data yet in all cards

- **testable**: true
- **target**: zsiga/dashboard.py::render_feedback_loop_section
- **Given** feedback metrics where `learnings_health == {total: 0, active: 0, top_patterns: [], last_write: None}`, `injection_rate == {implement_rate: "N/A", enrich_rate: "N/A", avg_injected: None}`, `auto_proposal_success == {total: 0, success: 0, failed: 0, stuck: 0, success_rate: "N/A", stuck_list: []}`, `self_assessment_coverage == {total_changes: 0, assessed: 0, coverage: "N/A", last_assessment: None}`
- **When** the dashboard HTML is rendered with these metrics
- **Then** the output HTML contains at least one instance of the text `"No data yet"`, and the section heading `"Feedback Loop"` is still present

#### Scenario: Partial data shows values where available and No data yet elsewhere

- **testable**: true
- **target**: zsiga/dashboard.py::render_feedback_loop_section
- **Given** feedback metrics where `learnings_health == {total: 5, active: 5, top_patterns: [...], last_write: "2025-06-01T00:00:00"}` but `injection_rate`, `auto_proposal_success`, and `self_assessment_coverage` are all empty defaults
- **When** the dashboard HTML is rendered with these metrics
- **Then** the output contains `"5"` (from learnings health total) AND `"No data yet"` (from at least one empty card)

---

### Requirement: Rendering Integration with Dashboard Pipeline

The existing dashboard rendering pipeline SHALL be extended to call the feedback loop metrics computation and include the resulting HTML section in its output. The integration SHALL be additive: existing sections (Model Usage, Phase Timing, Change History, etc.) SHALL remain unchanged in structure and content.

#### Scenario: Full dashboard render includes Feedback Loop without breaking existing sections

- **testable**: true
- **target**: zsiga/dashboard.py::render_feedback_loop_section
- **Given** a populated feedback metrics dict and the dashboard rendering context
- **When** the full dashboard page is rendered
- **Then** the output HTML contains `"Feedback Loop"` and also contains `"Change History"`, and the Feedback Loop section appears before the Change History section (index of "Feedback Loop" < index of "Change History" in the HTML string)

#### Scenario: Dashboard render does not crash with completely missing data sources

- **testable**: true
- **target**: zsiga/dashboard.py::render_feedback_loop_section
- **Given** feedback metrics computed from a non-existent learnings.jsonl and an empty database
- **When** the full dashboard page is rendered
- **Then** the output HTML is a valid string containing `"Feedback Loop"` and `"No data yet"`, and no exception is raised during rendering
