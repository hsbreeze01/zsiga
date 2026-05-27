# Spec: Verifier Layer 0 Integration Test Coverage

## ADDED Requirements

### Requirement: verify SHALL return None when Layer 0 checks fail

The `verify()` async function in `verifier.py` SHALL call `run_layer0_checks` as its
first step. When `layer0.all_passed` is `False`, it SHALL call `write_layer0_verify_md`
to write a FAIL `verify.md` and SHALL return `None` without invoking any LLM or
Layer 1 pytest.

#### Scenario: Layer 0 fail causes early return without LLM

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::verify
- **Given** a mocked `run_layer0_checks` returning `Layer0Result` with `all_passed=False`, and a mocked `AgentLoop`
- **When** `verify()` is called
- **Then** the return value is `None` and `write_layer0_verify_md` was called exactly once

---

### Requirement: verify SHALL proceed to Layer 1 when Layer 0 passes

When `layer0.all_passed` is `True`, `verify()` SHALL NOT call `write_layer0_verify_md`
and SHALL continue to execute `run_layer1_pytest` (Layer 1).

#### Scenario: Layer 0 pass allows Layer 1 execution

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::verify
- **Given** a mocked `run_layer0_checks` returning `Layer0Result` with `all_passed=True`, and mocked Layer 1 returning vacuous pass
- **When** `verify()` is called
- **Then** `write_layer0_verify_md` was NOT called and `run_layer1_pytest` was called
