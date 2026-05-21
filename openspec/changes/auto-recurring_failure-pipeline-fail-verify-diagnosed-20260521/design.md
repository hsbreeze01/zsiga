# Design: Fix Recurring `pipeline.fail.verify.diagnosed`

## Problem
All diagnose outcomes produce "Unconfirmed hypothesis" with no actionable info, causing the same failures to recur.

## Solution

### 1. Enhance `targeted_fix()` (diagnoser.py)
When no probe confirms a hypothesis, extract specific evidence from the error pattern:
- ImportError → extract module name, suggest install/import fix
- Lint error (E701 etc.) → extract file/line, suggest split
- AssertionError → describe test expectation mismatch
- Unknown → include first 120 chars of actual error as evidence

### 2. Reduce generic fallbacks in `hypothesize()`
Only add generic fallbacks if fewer than 3 specific hypotheses were generated. Always include at least one hypothesis referencing actual failure detail.

### 3. Add `verify_precheck()` function (diagnoser.py)
Lightweight pre-check that:
- Runs `python -c "import <module>"` on changed files to detect import errors
- Runs `ruff check` on changed files to detect lint errors
- Returns structured result: `{passed, error_type, file_path, message}`
- Completes in <30s, only inspects changed files

### 4. Integrate pre-check into orchestrator
Before LLM verify phase, call `verify_precheck()`. If it fails, skip LLM verify and enter eval-fix loop directly with specific error. Pass pre-check details to `_run_diagnosis()`.

### 5. Tests
- Unit tests for each new root-cause path in `test_diagnoser.py`
- Unit tests for `verify_precheck()` covering import/lint/pass cases
