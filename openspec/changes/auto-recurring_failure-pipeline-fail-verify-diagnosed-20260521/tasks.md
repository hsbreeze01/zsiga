# Tasks: Fix Recurring `pipeline.fail.verify.diagnosed`

## Group 1: Diagnoser Root-Cause Precision
- [ ] 1.1 Enhance `targeted_fix()` to produce specific fix descriptions with actionable evidence instead of "Unconfirmed hypothesis" — modify `zsiga/pipeline/diagnoser.py`
- [ ] 1.2 Reduce generic fallbacks in `hypothesize()` — only add fallbacks when < 3 specific hypotheses exist, ensure unknown pattern includes actual error snippet — modify `zsiga/pipeline/diagnoser.py`
- [ ] 1.3 Add unit tests for enhanced root-cause classification (ImportError, lint, AssertionError) in `tests/test_diagnoser.py`

## Group 2: Verify Pre-Check
- [ ] 2.1 Add `verify_precheck()` function to `zsiga/pipeline/diagnoser.py` — lightweight import + lint pre-check on changed files
- [ ] 2.2 Integrate `verify_precheck()` into orchestrator VERIFY phase — skip LLM verify on pre-check failure, pass details to diagnosis — modify `zsiga/pipeline/orchestrator.py`
- [ ] 2.3 Add unit tests for `verify_precheck()` in `tests/test_diagnoser.py` — import error, lint error, pass cases
