# Spec: Diagnostic Logging

## ADDED Requirements

### Requirement: Warning log when verdict is ISSUES_FOUND but no issues parsed

When `parse_review_verdict()` extracts a verdict of `ISSUES_FOUND` but
the issue extraction step produces an empty list, the function SHALL
emit a `WARNING` level log message containing at least the first 500
characters of the raw review.md content. This helps diagnose future
format drift without breaking the parsing flow.

The function SHALL still return `("ISSUES_FOUND", [])` in this case —
the logging is purely diagnostic and MUST NOT change the return value.

#### Scenario: Warning emitted when ISSUES_FOUND but zero issues

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: ISSUES_FOUND` but no recognizable issue pattern (no numbered, bullet, or bare `[SEVERITY]` markers)
- **When** `parse_review_verdict(change_dir)` is called
- **Then** a `WARNING` log is emitted containing a prefix of the raw content, and the return value is `("ISSUES_FOUND", [])`

#### Scenario: No warning when ISSUES_FOUND with valid issues

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: ISSUES_FOUND\n1. [CRITICAL] Some issue`
- **When** `parse_review_verdict(change_dir)` is called
- **Then** no `WARNING` log about empty issues is emitted, and the return value is `("ISSUES_FOUND", [{"severity": "CRITICAL", "description": "Some issue"}])`

#### Scenario: No warning when verdict is CLEAN

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: CLEAN`
- **When** `parse_review_verdict(change_dir)` is called
- **Then** no `WARNING` log about empty issues is emitted
