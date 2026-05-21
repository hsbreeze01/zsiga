# Spec: Verify Failure Root Cause Classification

## Problem

The `compute_stats` function in `metrics/collector.py` reports only an aggregate
`verify_pass_rate_pct`. There is no per-failure-category breakdown, so the
daemon cannot learn which failure category to prioritize fixing.

## ADDED Requirements

### Requirement: Verify failure root cause SHALL be classified into categories

The pipeline SHALL classify each verify failure into one of the following
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

Classification SHALL follow a priority order: `precheck_import` > `precheck_syntax` > `lint` > `test` > `layer1_pytest` > `llm_judge` > `unknown`. When multiple failure signals exist, the highest-priority category SHALL be returned.

#### Scenario: Classify lint failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify.md` content containing "E701 Multiple statements on one line" and mech_results showing `lint.passed=False`, `test.passed=True`
- **When** `classify_verify_failure` is called with that content and mech_results
- **Then** it SHALL return the string `"lint"`

#### Scenario: Classify test failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify.md` content containing "FAILED test_foo.py::test_bar" and mech_results showing `test.passed=False`, `lint.passed=True`
- **When** `classify_verify_failure` is called
- **Then** it SHALL return the string `"test"`

#### Scenario: Classify layer1_pytest failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `layer1_result` showing `{"passed": false, "vacuous": false}` and no lint/test mech failures
- **When** `classify_verify_failure` is called with the verify.md content and layer1_result
- **Then** it SHALL return the string `"layer1_pytest"`

#### Scenario: Classify unknown when no verify.md

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** an empty string for verify.md content and no mech_results, layer1_result, or precheck_error_type
- **When** `classify_verify_failure` is called
- **Then** it SHALL return the string `"unknown"`

#### Scenario: Classify llm_judge when no mechanical failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify.md` content with verdict "FAIL", Layer 1 marked as "vacuous", and mech_results showing `test.passed=True`, `lint.passed=True`
- **When** `classify_verify_failure` is called
- **Then** it SHALL return the string `"llm_judge"`

#### Scenario: Classify precheck_import

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** `verify.md` content mentioning "Pre-check failure (import)" and `precheck_error_type="import"`
- **When** `classify_verify_failure` is called
- **Then** it SHALL return the string `"precheck_import"`

### Requirement: Verify failure category SHALL be persisted in PhaseRecord

`PhaseRecord` SHALL accept an optional `failure_category` field. When present,
it SHALL be serialized by `to_dict()`.

#### Scenario: Failure category recorded in PhaseRecord

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a `PhaseRecord` for phase=VERIFY with outcome=FAIL
- **When** the record is created with `failure_category="lint"`
- **Then** `PhaseRecord.to_dict()` SHALL include the key `"failure_category"` with value `"lint"`

#### Scenario: PhaseRecord without failure_category serializes without error

- **testable**: true
- **target**: zsiga/metrics/types.py::PhaseRecord
- **Given** a `PhaseRecord` for phase=VERIFY with outcome=SUCCESS and no `failure_category`
- **When** `to_dict()` is called
- **Then** the dict SHALL NOT raise an error, and `failure_category` SHALL be `None` or absent

### Requirement: compute_stats SHALL report verify failure breakdown

#### Scenario: Verify failure breakdown in stats output

- **testable**: true
- **target**: zsiga/metrics/collector.py::compute_stats
- **Given** a list of 3 changes, each containing one verify-phase record with outcome="fail"; two with `failure_category="lint"` and one with `failure_category="test"`
- **When** `compute_stats` is called
- **Then** the returned dict SHALL contain key `"verify_failure_breakdown"` mapping `{"lint": 2, "test": 1}`
