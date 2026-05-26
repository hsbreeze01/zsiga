# Verifier Layer 0 Integration Tests

## ADDED Requirements

### Requirement: verify() returns None on Layer 0 failure
The `verify()` function in `verifier.py` SHALL call `run_layer0_checks` first. If `layer0.all_passed` is `False`, `verify()` SHALL write a `verify.md` with `Verdict: FAIL` via `write_layer0_verify_md`, return `None`, and NOT proceed to Layer 1 pytest or Layer 2 LLM judge.

#### Scenario: verify returns None when Layer 0 fails

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::verify
- **Given** a mock `run_layer0_checks` that returns a `Layer0Result` with `all_passed=False`
- **When** `verify()` is called
- **Then** it returns `None` and `verify.md` is written containing `Verdict: FAIL`

#### Scenario: verify proceeds to Layer 1 when Layer 0 passes

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::verify
- **Given** a mock `run_layer0_checks` that returns a `Layer0Result` with `all_passed=True`
- **When** `verify()` is called
- **Then** execution proceeds past the Layer 0 guard block (Layer 1 pytest is invoked)
