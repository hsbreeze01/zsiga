# fix-review-verdict-parser

## Summary
Fix the review phase verdict/issue parser to handle the actual output formats produced by the critic sub-agent, so review detail fields are no longer empty and CRITICAL issues are correctly detected.

## Problem
The review phase has a 2.8% pass rate (1/36) across 50 recent proposals. 34 out of 36 review records have an empty `detail` field in the database. This means:

1. **Review is not acting as a quality gate** — ISSUES_FOUND verdict is recorded as FAIL, but CRITICAL issues are never extracted, so no fix is triggered.
2. **Root cause analysis is impossible** — empty detail fields mean we can't tell what the reviewer actually found.
3. **Misleading metrics** — the 2.8% pass rate reflects parser failures, not actual code quality issues.

### Technical Root Cause

The critic sub-agent (using the `review` role) writes `review.md` via `write_file`. However, due to the model's behavior (glm-5.1), the actual file content often contains:

- **Tool call XML artifacts**: `<tool_calling>` / `<tool_call:` wrappers around the actual content
- **Mixed format**: The `Verdict: CLEAN/ISSUES_FOUND` line is present (the verdict regex matches), but the issues list uses inconsistent formatting:
  - Sometimes uses `1. [CRITICAL] ...` (expected by parser)
  - Sometimes uses `- [CRITICAL] ...` (bullet points)
  - Sometimes issues are embedded in prose paragraphs
  - Sometimes issues span multiple lines with indentation

There IS a cleanup function `_extract_clean_review()` in `run_review()`, but:
- It only fires when review.md doesn't exist OR contains tool_call artifacts in first 300 chars
- Its issue extraction regex is identical to `parse_review_verdict`'s, so it has the same format limitations
- The cleaned content may still not match the strict `N. [SEVERITY] description` pattern

### Evidence

- `cleanup-stale-test-files/review.md`: Contains Chinese text + tool_call XML, no structured verdict
- `validate-pipeline-fixes-20260520/review.md`: Contains `<tool_call:` XML wrapping a proper `write_file` with `Verdict: ISSUES_FOUND` and 4 numbered CRITICAL items — but the XML wrapper prevented parsing
- `add-health-check-endpoint/review.md`: Contains `<tool_calling>` XML wrapping a `write_file` with `Verdict: CLEAN` — cleanup worked for CLEAN but issues list parsing is the gap

## Technical Design

### File: `zsiga/agent/reviewer.py`

**Change 1: Robust issue extraction in `_extract_clean_review()`**
- Replace the single strict regex with multiple fallback patterns:
  1. `N. [SEVERITY] description` (current strict)
  2. `- [SEVERITY] description` (bullet list)
  3. `[SEVERITY] description` (no number/bullet)
- Strip XML tags from issue descriptions
- Join multi-line descriptions (stop at next issue marker or blank line)

**Change 2: Always sanitize review.md before parsing**
- Move the sanitization logic from `run_review()` into `parse_review_verdict()` as a preprocessing step
- This ensures even if `run_review()` cleanup fails or is bypassed, parsing still works

**Change 3: Enhanced logging**
- When issues list is empty but verdict is ISSUES_FOUND, log the raw content (first 500 chars) at WARNING level
- This helps diagnose future format drift

### Flow After Fix

```
Critic writes review.md (possibly with XML artifacts)
    ↓
run_review() sanitizes file (existing cleanup, improved)
    ↓
parse_review_verdict() preprocesses content (NEW: strip XML, normalize)
    ↓
Multiple regex patterns try to extract issues (NEW: fallback patterns)
    ↓
If verdict=ISSUES_FOUND but 0 issues parsed → WARNING log with raw content
    ↓
Issues correctly populated → _has_critical() works → fix triggered when needed
```

## Acceptance Criteria
1. `parse_review_verdict()` successfully extracts issues from ALL 3 format variants (numbered, bulleted, bare)
2. XML tool_call artifacts are stripped before parsing
3. When verdict=ISSUES_FOUND but 0 issues are parsed, a WARNING log is emitted with first 500 chars of content
4. Existing CLEAN verdict parsing is unaffected (no regression)
5. `ruff check zsiga/agent/reviewer.py` passes
6. No new dependencies added

## Scope
- In scope: `zsiga/agent/reviewer.py` — `_extract_clean_review()`, `parse_review_verdict()`, sanitization logic
- Out of scope: Review prompt changes, sub-agent behavior changes, other pipeline phases

## Risk
- Impact: Medium — review phase is already broken (2.8% pass rate), so improvement has low downside
- Reversibility: Single file change, fully git-revertible
- Testing: Can verify by running parse_review_verdict against archived review.md files
