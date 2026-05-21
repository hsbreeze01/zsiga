# Spec: Verify Failure Root Cause Classification

## Problem

The `compute_stats` function in `metrics/collector.py` reports only an aggregate
`verify_pass_rate_pct`. There is no per-failure-category breakdown, so the
daemon cannot learn which failure category to prioritize fixing.

## ADDED Requirements

### Requirement: Verify failure root cause SHALL be classified into categories

The orchestrator SHALL classify each verify failure into one of the following
categories based on the content of `verify.md` and mechanical check results:

| Category            | Detection heuristic                                         |
|---------------------|-------------------------------------------------------------|
| `lint`              | `verify.md` or mech_results contains lint error codes       |
| `test`              | `verify.md` or mech_results contains pytest failure output  |
| `layer1_pytest`     | `verify_layer1.json` shows `passed=false`                   |
| `must_modify_gate`  | must-modify coverage < 80%                                  |
| `precheck_import`   | `verify_precheck` error_type == "import"                    |
| `precheck_syntax`   | `verify_precheck` error_type == "syntax"                    |
| `llm_judge`         | None of the above match (LLM wrote FAIL for Layer-2 reason)|
| `unknown`           | No `verify.md` content available                            |

#### Scenario: Classify lint failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify.md` content containing "E701 Multiple statements on one line" and "ruff check" in the output
- **When** `classify_verify_failure` is called with that content and `mech_results` showing `lint.passed=False`
- **Then** it SHALL return the string `"lint"`

#### Scenario: Classify test failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify.md` content containing "FAILED test_foo.py::test_bar" and `mech_results` showing `test.passed=False`
- **When** `classify_verify_failure` is called
- **Then** it SHALL return the string `"test"`

#### Scenario: Classify layer1_pytest failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify_layer1.json` showing `{"passed": false, "vacuous": false}` and no lint/test mech failures
- **When** `classify_verify_failure` is called with the Layer 1 result loaded
- **Then** it SHALL return the string `"layer1_pytest"`

#### Scenario: Classify unknown when no verify.md

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** an empty string for verify.md content and no mech_results
- **When** `classify_verify_failure` is called
- **Then** it SHALL return the string `"unknown"`

### Requirement: Verify failure category SHALL be persisted in PhaseRecord

#### Scenario: Failure category recorded in PhaseRecord

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a `PhaseRecord` for phase="verify" with outcome="fail"
- **When** the record is created with a `failure_category="lint"` field
- **Then** `PhaseRecord.to_dict()` SHALL include the key `"failure_category"` with value `"lint"`

### Requirement: compute_stats SHALL report verify failure breakdown

#### Scenario: Verify failure breakdown in stats output

- **testable**: true
- **target**: zsiga/metrics/collector.py::compute_stats
- **Given** a list of changes containing 3 verify failures with `failure_category` values `"lint"`, `"test"`, and `"lint"`
- **When** `compute_stats` is called
- **Then** the returned dict SHALL contain a key `"verify_failure_breakdown"` mapping category names to counts, where `"lint": 2` and `"test": 1`
