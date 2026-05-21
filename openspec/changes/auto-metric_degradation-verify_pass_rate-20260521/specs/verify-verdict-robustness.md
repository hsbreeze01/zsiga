# Spec: Verify Verdict Parsing Robustness

## ADDED Requirements

### Requirement: Verdict parsing SHALL handle common LLM formatting variations

The `read_verdict` function MUST parse the verifier's output reliably even when the LLM introduces minor formatting variations. The function SHALL accept any of the following patterns as valid verdicts:
- `Verdict: PASS` or `Verdict: FAIL` (canonical format)
- `**Verdict: PASS**` or `**Verdict: FAIL**` (bold markdown)
- `Verdict:  PASS` or `Verdict:  FAIL` (extra whitespace)

If no verdict pattern is found after attempting all variations, the function SHALL return `"UNKNOWN"` and log a warning.

#### Scenario: Parse canonical verdict
- **Given** `verify.md` contains `Verdict: PASS`
- **When** `read_verdict` is called
- **Then** it SHALL return `"PASS"`

#### Scenario: Parse bold-formatted verdict
- **Given** `verify.md` contains `**Verdict: FAIL**`
- **When** `read_verdict` is called
- **Then** it SHALL return `"FAIL"`

#### Scenario: Parse verdict with extra whitespace
- **Given** `verify.md` contains `Verdict:  PASS` (two spaces)
- **When** `read_verdict` is called
- **Then** it SHALL return `"PASS"`

#### Scenario: No parseable verdict in output
- **Given** `verify.md` contains `The implementation looks good but I couldn't determine a clear verdict.`
- **When** `read_verdict` is called
- **Then** it SHALL return `"UNKNOWN"`

### Requirement: UNKNOWN verdict SHALL be treated as FAIL in pipeline flow

When `read_verdict` returns `"UNKNOWN"`, the orchestrator SHALL treat it identically to `"FAIL"` for the purposes of pipeline progression — triggering the eval fix loop and potential revert.

This is existing behavior — this requirement merely documents it for clarity. The `verify_outcome` calculation already maps any non-"PASS" verdict to `Outcome.FAIL`.

#### Scenario: UNKNOWN verdict triggers fix loop
- **Given** the verifier LLM produces a `verify.md` with no parseable Verdict line
- **When** the orchestrator reads the verdict
- **Then** it SHALL enter the eval fix loop, same as for Verdict: FAIL
