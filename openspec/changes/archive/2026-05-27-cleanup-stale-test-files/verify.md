Verdict: PASS
Layer 1: vacuous — no test file `tests/test_spec_cleanup_stale_test_files__stale_test_removal.py` exists; all scenarios evaluated at Layer 2
Completeness: ✓ All six scenarios across both requirements are satisfied — stale `test_spec_*` files are deleted, non-spec files and conftest are untouched, no paths outside `tests/` appear in the diff, and the remaining test suite passes (pre-run ✅ PASSED).
Correctness: ✓ The git diff consists exclusively of deletions of `test_spec_*.py` files under `tests/`; no modifications to any other file, satisfying both the removal requirement and the no-side-effects requirement.
Coherence: ✓ The change is a pure cleanup — only deletion of orphaned test files, with no source or configuration changes, fully aligned with the spec intent.
Issues: none
