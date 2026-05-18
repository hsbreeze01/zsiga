# Tasks: Command Timeout Tracking

## 1. Backend — Timeout Detection

- [ ] 1.1 Add timeout detection in orchestrator: check RunResult content for "TIMEOUT" after enrich/implement/verify calls, record `Outcome.TIMEOUT` in PhaseRecord when detected
  - Files: `zsiga/pipeline/orchestrator.py`
  - Add `_is_timeout(result)` helper, apply in ENRICH, IMPLEMENT, VERIFY phases of `_run_phases()`

## 2. Backend — Stats Computation

- [ ] 2.1 Add per-phase `timeout_rate` computation and top-level `timeout_stats` to `compute_stats()` in collector
  - Files: `zsiga/metrics/collector.py`
  - Count timeout outcomes per phase, compute rate, find worst phase, find phases above 20%
  - Add `timeout_rate: 0` to `_empty_stats()` phase entries

## 3. Backend — Dashboard Rendering

- [ ] 3.1 Add timeout rate column to phase table and timeout warning banner + summary card to dashboard
  - Files: `zsiga/metrics/dashboard.py`
  - Modify `_phase_table()` to add Timeout Rate column with color coding
  - Add conditional warning banner before phase section in `_render()`
  - Add ⏱️ Timeout Rate card to the stats grid in `_render()`

## 4. Tests

- [ ] 4.1 Add tests for timeout detection, stats computation, and dashboard rendering
  - Files: `tests/test_timeout_tracking.py` (new)
  - Test orchestrator timeout detection with mock RunResult
  - Test collector timeout_rate computation with fixture data
  - Test dashboard HTML contains timeout rate column and warning banner
