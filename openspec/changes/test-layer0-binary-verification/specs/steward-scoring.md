# Steward Scoring and Threshold Tests

## ADDED Requirements

### Requirement: Steward prompt contains 6 evaluation dimensions
The `_STEWARD_PROMPT` in `roles.py` SHALL include exactly 6 evaluation dimensions, each scored 0-2, for a total maximum of /12. The dimensions SHALL include "验收可测性" (Eval). The prompt SHALL reference `/12` as the total.

#### Scenario: steward prompt includes 6 dimensions and 12 total

- **testable**: true
- **target**: zsiga/agent/roles.py
- **Given** the `_STEWARD_PROMPT` string from `roles.py`
- **When** its content is examined
- **Then** it contains the text "验收可测性" and contains the pattern "/12" indicating a 12-point scale

---

### Requirement: _parse_verdict supports /12 and /10 score formats
`_parse_verdict` in `proposal_gate.py` SHALL extract the numeric score from text containing `总分: N/12` or `总分: N/10`. The score SHALL be the integer before the slash.

#### Scenario: parse_verdict extracts score from /12 format

- **testable**: true
- **target**: zsiga/pipeline/proposal_gate.py::_parse_verdict
- **Given** review text containing `总分: 10/12`
- **When** `_parse_verdict` is called
- **Then** the returned score is `10`

#### Scenario: parse_verdict extracts score from /10 format for backward compatibility

- **testable**: true
- **target**: zsiga/pipeline/proposal_gate.py::_parse_verdict
- **Given** review text containing `总分: 7/10`
- **When** `_parse_verdict` is called
- **Then** the returned score is `7`

---

### Requirement: PipelineConfig default scoring thresholds
`PipelineConfig` SHALL default `proposal_gate_score_accept` to `10` and `proposal_gate_score_pushback` to `6`.

#### Scenario: PipelineConfig has correct default thresholds

- **testable**: true
- **target**: zsiga/config.py
- **Given** a `PipelineConfig` instance created with default arguments
- **When** `proposal_gate_score_accept` and `proposal_gate_score_pushback` are accessed
- **Then** `proposal_gate_score_accept` is `10` and `proposal_gate_score_pushback` is `6`
