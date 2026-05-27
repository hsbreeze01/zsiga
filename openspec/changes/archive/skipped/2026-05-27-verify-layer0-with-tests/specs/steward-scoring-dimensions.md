# Spec: Steward Scoring Dimensions Test Coverage

## ADDED Requirements

### Requirement: Steward prompt SHALL define 6 scoring dimensions on 12-point scale

`_STEWARD_PROMPT` in `roles.py` SHALL contain 6 evaluation dimensions, each scored
0-2, with a total expressed as `/12`. The dimensions SHALL include 可行性 (Feasibility),
可执行性 (Actionability), 能力匹配 (Capability), 历史风险 (History Risk),
范围合理性 (Scope), and 验收可测性 (Eval).

#### Scenario: Steward prompt contains 6 dimensions and 12-point scale

- **testable**: true
- **target**: zsiga/agent/roles.py::_STEWARD_PROMPT
- **Given** `_STEWARD_PROMPT` is loaded from `roles.py`
- **When** the text is inspected
- **Then** it contains all 6 dimension names AND contains `/12`

---

### Requirement: _parse_verdict SHALL parse 12-point scores

`_parse_verdict(text)` in `proposal_gate.py` SHALL extract both the verdict keyword
(ACCEPT/PUSHBACK/REJECT) and a numeric score from text. It SHALL support the `/12`
format via regex `总分:\s*(\d+)\s*/\s*(?:10|12)`.

#### Scenario: Parse verdict with 12-point score

- **testable**: true
- **target**: zsiga/pipeline/proposal_gate.py::_parse_verdict
- **Given** text containing `## Verdict: PUSHBACK` and `总分: 10/12`
- **When** `_parse_verdict` is called
- **Then** the result is `(GateVerdict.PUSHBACK, 10)`

---

### Requirement: _parse_verdict SHALL be backward-compatible with 10-point scores

The same regex in `_parse_verdict` SHALL also match `/10` format, allowing
backward compatibility with older steward verdict texts.

#### Scenario: Parse verdict with 10-point score fallback

- **testable**: true
- **target**: zsiga/pipeline/proposal_gate.py::_parse_verdict
- **Given** text containing `## Verdict: ACCEPT` and `总分: 7/10`
- **When** `_parse_verdict` is called
- **Then** the result is `(GateVerdict.ACCEPT, 7)`

---

### Requirement: PipelineConfig SHALL have correct default gate thresholds

`PipelineConfig` in `config.py` SHALL provide `proposal_gate_score_accept` defaulting
to `10` and `proposal_gate_score_pushback` defaulting to `6`, matching the 12-point
steward scale decision rules.

#### Scenario: Default config thresholds match 12-point scale

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** a default `PipelineConfig()` instance
- **When** attributes are read
- **Then** `proposal_gate_score_accept` is `10` and `proposal_gate_score_pushback` is `6`
