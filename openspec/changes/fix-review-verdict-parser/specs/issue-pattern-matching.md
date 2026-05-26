# Spec: Issue Pattern Matching

## MODIFIED Requirements

### Requirement: Multi-pattern issue extraction

`parse_review_verdict()` SHALL extract severity and description from issues
listed in any of the following formats, tried in fallback order:

1. Numbered list: `1. [SEVERITY] description`
2. Bullet list: `- [SEVERITY] description`
3. Bare severity: `[SEVERITY] description`

Where `SEVERITY` is `CRITICAL` or `SUGGESTION`.

When content matches multiple patterns, the parser SHALL extract all
distinct issues regardless of which pattern each individual issue uses.

#### Scenario: Numbered list issues are extracted

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: ISSUES_FOUND` followed by numbered issues like `1. [CRITICAL] Missing error handling\n2. [SUGGESTION] Variable naming`
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("ISSUES_FOUND", [{"severity": "CRITICAL", "description": "Missing error handling"}, {"severity": "SUGGESTION", "description": "Variable naming"}])`

#### Scenario: Bullet list issues are extracted

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: ISSUES_FOUND` followed by bullet issues like `- [CRITICAL] Dead code detected\n- [SUGGESTION] Add type hints`
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("ISSUES_FOUND", [{"severity": "CRITICAL", "description": "Dead code detected"}, {"severity": "SUGGESTION", "description": "Add type hints"}])`

#### Scenario: Bare severity issues are extracted

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: ISSUES_FOUND` followed by bare issues like `[CRITICAL] Missing import\n[SUGGESTION] Use f-string`
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("ISSUES_FOUND", [{"severity": "CRITICAL", "description": "Missing import"}, {"severity": "SUGGESTION", "description": "Use f-string"}])`

#### Scenario: Multi-line issue description is merged

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing an issue whose description spans multiple lines before the next issue marker or blank line
- **When** `parse_review_verdict(change_dir)` is called
- **Then** the issue's description includes the full multi-line text (excluding the next issue marker)

#### Scenario: Mixed format issues are all extracted

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: ISSUES_FOUND` followed by a mix of numbered, bullet, and bare format issues
- **When** `parse_review_verdict(change_dir)` is called
- **Then** all issues are extracted with correct severity and non-empty descriptions

### Requirement: CLEAN verdict backward compatibility

`parse_review_verdict()` SHALL continue to return `("CLEAN", [])` for
review content containing `Verdict: CLEAN` without any issue extraction
attempt. This is a backward-compatible requirement — existing behavior
MUST NOT regress.

#### Scenario: CLEAN verdict returns empty issues list

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` file containing `Verdict: CLEAN\n\nAll specs covered.`
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("CLEAN", [])`
