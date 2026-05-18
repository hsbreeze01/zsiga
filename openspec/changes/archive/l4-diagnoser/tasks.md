# Tasks: l4-diagnoser

## Group 1: Core Diagnoser Module

- [x] 1.1 Create `zsiga/pipeline/diagnoser.py` with data models (Hypothesis, ProbeResult, FixPlan, DiagnosisReport) and Diagnoser class implementing `hypothesize()`, `instrument()`, `targeted_fix()` with rule-based hypothesis generation from error patterns

## Group 2: Agent Role Registration

- [x] 2.1 Add `DIAGNOSER` enum value to `Role` in `zsiga/agent/roles.py` and register its `RoleConfig` with read-only tools and diagnosis-specific system prompt

## Group 3: Orchestrator Integration

- [x] 3.1 Integrate Diagnoser into `zsiga/pipeline/orchestrator.py` — invoke `diagnose()` in `_run_phases()` when eval-fix loop exhausts (verify FAIL path), save DiagnosisReport, and record a lesson with pattern_key `pipeline.fail.verify.diagnosed`

## Group 4: Tests

- [x] 4.1 Create `tests/test_diagnoser.py` with unit tests covering: hypothesis generation from various error patterns (ImportError, AssertionError, lint errors), instrumentation produces read-only probe results, targeted fix picks confirmed hypothesis, DiagnosisReport markdown generation and persistence
