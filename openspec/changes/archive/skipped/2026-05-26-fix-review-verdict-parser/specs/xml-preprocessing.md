# Spec: XML Preprocessing

## ADDED Requirements

### Requirement: XML artifact stripping before parsing

`parse_review_verdict()` SHALL preprocess review.md content to remove
XML tool-call artifacts before attempting verdict and issue extraction.
This preprocessing SHALL handle at minimum the following XML patterns:

- `<tool_call:...>...</tool_call:>` (self-closing variant with colon)
- `<tool_calling>...</tool_calling>` (wrapper variant)
- `<tool_call_layout>...</tool_call_layout>` (layout container)

After stripping, the remaining text MUST still contain the `Verdict:` line
and any issue list. The parser SHALL NOT fail or return `UNKNOWN` solely
because XML artifacts are present.

#### Scenario: Verdict extracted from tool_call colon wrapper

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` whose content is wrapped in `<tool_call:write_file>...content: Verdict: CLEAN\n...\n</tool_call:>` XML
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("CLEAN", [])`

#### Scenario: Issues extracted from tool_calling wrapper with numbered list

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` whose content is wrapped in `<tool_calling>...content: Verdict: ISSUES_FOUND\n1. [CRITICAL] Missing error handling\n2. [SUGGESTION] Naming issue\n...</tool_calling>` XML
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("ISSUES_FOUND", [{"severity": "CRITICAL", ...}, {"severity": "SUGGESTION", ...}])` with 2 issues

#### Scenario: Issues extracted from tool_call_layout wrapper with bullet list

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` whose content is wrapped in `<tool_call_layout>...Verdict: ISSUES_FOUND\n- [CRITICAL] Dead code\n- [SUGGESTION] Add docstring\n...</tool_call_layout>` XML
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("ISSUES_FOUND", [{"severity": "CRITICAL", ...}, {"severity": "SUGGESTION", ...}])` with 2 issues

#### Scenario: Nested XML with invoke and parameter tags is stripped

- **testable**: true
- **target**: zsiga/agent/reviewer.py::parse_review_verdict
- **Given** a `review.md` whose content contains `<invoke name="write_file"><parameter name="content">Verdict: ISSUES_FOUND\n1. [CRITICAL] Bug</parameter></invoke>` XML
- **When** `parse_review_verdict(change_dir)` is called
- **Then** it returns `("ISSUES_FOUND", [{"severity": "CRITICAL", "description": "Bug"}])`
