# Spec: Robust Issue Pattern Matching

## Requirement
`parse_review_verdict()` must extract severity and description from these formats:

### Pattern 1: Numbered list (current strict — already works)
```
1. [CRITICAL] description text
2. [SUGGESTION] description text
```

### Pattern 2: Bullet list (currently fails)
```
- [CRITICAL] description text
- [SUGGESTION] description text
```

### Pattern 3: No marker (currently fails)
```
[CRITICAL] description text
[SUGGESTION] description text
```

### Pattern 4: Issues in XML-wrapped content (partially works after cleanup)
```
<tool_call: ...>
content: Verdict: ISSUES_FOUND
1. [CRITICAL] description
</tool_call:>
```

### Edge Cases
- Multi-line description: issue continues on next line, stops at next issue marker or double newline
- Description containing `[` or `]` characters (not severity markers)
- Whitespace variations: extra spaces, tabs

## Implementation
Add fallback regex patterns in `parse_review_verdict()`, tried in order:
1. Current: `\d+\.\s*\[(CRITICAL|SUGGESTION)\]\s*(.+?)(?=\n\d+\.|$)`
2. New: `-\s*\[(CRITICAL|SUGGESTION)\]\s*(.+?)(?=\n- |$)`
3. New: `\[(CRITICAL|SUGGESTION)\]\s*(.+?)(?=\n\[|$)`

Each pattern tries in sequence; first match wins for each issue position.

## Acceptance Test
Given review.md content with any of the 4 patterns, `parse_review_verdict()` returns the correct number of issues with correct severity and non-empty descriptions.
