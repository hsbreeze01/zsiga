# Design: Structured Diagnosis Loop (l4-diagnoser)

## Architecture Decision

**Decision**: Implement `Diagnoser` as a pure Python class (no LLM calls in core logic) that performs rule-based hypothesis generation and read-only instrumentation. The orchestrator calls it synchronously before reverting on verify failure.

**Rationale**: The current `_eval_fix_loop` blindly re-sends errors to the LLM fix engine with the same prompt pattern. A structured diagnosis layer that extracts error patterns → generates ranked hypotheses → probes minimally → produces a targeted fix plan gives the fix engine better context, reducing wasted turns. Keeping Diagnoser rule-based (no LLM) avoids additional API cost and latency.

## Data Flow

```
verify FAIL (after eval-fix exhausted)
       │
       ▼
  orchestrator calls diagnose()
       │
       ▼
  Diagnoser.hypothesize(failure_info)
       │  - Parses error output for known patterns (ImportError, AssertionError, lint codes)
       │  - Generates 3-5 Hypothesis objects ranked by confidence
       │
       ▼
  Diagnoser.instrument(hypotheses, target_path, transport)
       │  - For top 3 hypotheses, runs read-only probes:
       │    - read_file to check source
       │    - search/ast_search to find related code
       │    - diagnostics to check lint issues
       │  - Marks each hypothesis confirmed/denied with evidence
       │
       ▼
  Diagnoser.targeted_fix(hypotheses)
       │  - Picks confirmed hypothesis (or best unconfirmed)
       │  - Generates FixPlan with root_cause, fix_description, affected_files
       │
       ▼
  DiagnosisReport written to {change_dir}/diagnosis.md
       │
       ▼
  record_lesson() with pattern_key "pipeline.fail.verify.diagnosed"
       │
       ▼
  orchestrator proceeds to revert (or optionally retry with FixPlan context)
```

## Data Models

### Hypothesis
```python
@dataclass
class Hypothesis:
    rank: int           # 1-based, sorted by confidence
    description: str    # Human-readable root cause description
    confidence: float   # 0.0–1.0
    evidence: str       # Supporting evidence from error text
    probe_result: Optional[ProbeResult] = None
```

### ProbeResult
```python
@dataclass
class ProbeResult:
    confirmed: bool
    evidence: str
    probe_type: str     # "file_read", "search", "diagnostics", "bash"
```

### FixPlan
```python
@dataclass
class FixPlan:
    root_cause: str
    fix_description: str
    affected_files: list[str]
    confirmed: bool     # Whether root cause was confirmed by probe
```

### DiagnosisReport
```python
@dataclass
class DiagnosisReport:
    change_name: str
    hypotheses: list[Hypothesis]
    confirmed_hypothesis: Optional[Hypothesis]
    fix_plan: FixPlan
    timestamp: str

    def to_markdown() -> str
    def save(change_dir, transport) -> None
```

## Hypothesis Generation Rules (Rule-Based)

The `hypothesize()` method uses pattern matching on the failure detail:

| Error Pattern | Hypothesis Description | Confidence |
|---|---|---|
| `ImportError` / `ModuleNotFoundError` | Missing or incorrect import | 0.9 |
| `AssertionError` | Test expectation mismatch | 0.8 |
| `NameError` | Undefined variable or missing import | 0.85 |
| `SyntaxError` / lint codes (E701, E702, E501...) | Code style/syntax violation | 0.75 |
| `TypeError` | Type mismatch in function call | 0.7 |
| `AttributeError` | Missing attribute or wrong object type | 0.7 |
| Generic test failure (`FAILED` in output) | Test assertion failed | 0.6 |
| Timeout | Execution exceeded time budget | 0.5 |

Falls back to generic "unknown error" hypothesis if no pattern matches.

## Instrumentation Probes

Each probe is read-only:

1. **File read probe**: Read the file mentioned in the error traceback, check if the problematic line/variable/import exists
2. **Search probe**: `search()` for the symbol mentioned in the error to find its definition
3. **Diagnostics probe**: Run `ruff check` on the affected file for lint issues
4. **AST probe**: `ast_search()` for the pattern that might be wrong (e.g., `import $X` to verify imports)

## Files to Create/Modify

### New Files
1. `zsiga/pipeline/diagnoser.py` — Core Diagnoser class with Hypothesis, ProbeResult, FixPlan, DiagnosisReport dataclasses

### Modified Files
2. `zsiga/agent/roles.py` — Add `DIAGNOSER` role to the `_ROLES` dict and `Role` enum
3. `zsiga/pipeline/orchestrator.py` — Add `diagnose()` call in `_run_phases()` before final revert on verify failure
4. `tests/test_diagnoser.py` — Unit tests for Diagnoser (hypothesize, instrument, targeted_fix, report generation)
