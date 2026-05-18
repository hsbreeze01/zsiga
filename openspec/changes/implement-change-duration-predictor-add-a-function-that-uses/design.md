# Design: Change Duration Predictor

## Architecture Decision

Create a new module `zsiga/duration_predictor.py` as a pure-function library with no external dependencies beyond the Python standard library. This keeps the predictor lightweight, testable, and easy to import from any part of the agent pipeline.

## Data Flow

```
historical phase_stats (list of dicts)
        │
        ▼
┌─────────────────────────────┐
│ predict_change_duration()   │
│                             │
│  1. Validate input          │
│  2. If < 3 records:         │
│     → return fallback       │
│  3. For each known phase:   │
│     a. Collect (x, y) pairs │
│     b. Fit linear model     │
│     c. Predict & clamp      │
│  4. Compute _total          │
│  5. Return result dict      │
└─────────────────────────────┘
        │
        ▼
  { phase: seconds, ..., "_total": float }
```

## Linear Model (per phase)

For each phase (explore, design, implement, verify, deliver):

```
features: x₁ = project_lines, x₂ = proposal_chars
target:  y = duration_seconds

Fit: y = a·x₁ + b·x₂ + c  (least squares via normal equations)
```

The normal equations are solved using a small 3×3 system. No numpy/scipy needed — we implement the closed-form solution with pure Python arithmetic (sum, zip, basic math). This is sufficient because:
- The feature space is only 2-dimensional
- Historical records are typically < 100 entries
- Numerical stability is not a concern at this scale

## Fallback Strategy

When fewer than 3 historical records are available:
1. Compute median of available durations per phase
2. If no data exists for a phase, use a hardcoded default of 30.0 seconds
3. Median is robust to outliers compared to mean

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `zsiga/duration_predictor.py` | **CREATE** | Core module with `predict_change_duration()`, `_fit_linear()`, `_predict_phase()`, `_fallback_estimates()` |
| `tests/test_phase_duration.py` | **MODIFY** | Add tests for the new predictor (file already exists for related tests) |

## Key Design Principles

1. **Pure functions**: No I/O, no class state, no side effects. All data passed as arguments.
2. **No new dependencies**: Uses only `statistics.median` from stdlib.
3. **Defensive**: Handles missing phase keys, negative predictions, empty input gracefully.
4. **Testable**: Each internal function (`_fit_linear`, `_predict_phase`, `_fallback_estimates`) is independently testable.
