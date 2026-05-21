# Spec: Diagnoser Root-Cause Precision

## MODIFIED Requirements

### Requirement: Root-Cause Classification SHALL Be Specific

The `Diagnoser.targeted_fix()` method MUST produce actionable root-cause descriptions. When no probe confirms a hypothesis, the fix description SHALL NOT use the phrase "Unconfirmed hypothesis" or "Needs further investigation" alone — it MUST include the best-available evidence and a concrete suggested action derived from the matched error pattern.

#### Scenario: ImportError produces specific root cause even without probe confirmation

- **Given** a failure detail containing `ImportError: No module named 'some_module'`
- **And** all probes return `confirmed=False` (e.g., module not found in codebase)
- **When** `targeted_fix()` is called
- **Then** the returned `FixPlan.fix_description` SHALL contain:
  - the module name extracted from the error (`some_module`)
  - a concrete action (e.g., "Add missing import for 'some_module'" or "Install dependency providing 'some_module'")
- **And** `FixPlan.confirmed` SHALL be `False`
- **And** `FixPlan.fix_description` SHALL NOT equal the generic string `"Unconfirmed hypothesis: … Needs further investigation."`

#### Scenario: Lint error produces specific root cause even without probe confirmation

- **Given** a failure detail containing `E701 Multiple statements on one line (colon)` with a file path like `src/foo.py:42`
- **And** all probes return `confirmed=False`
- **When** `targeted_fix()` is called
- **Then** the returned `FixPlan.fix_description` SHALL mention the lint rule (`E701`), the file path, and a concrete suggestion (e.g., "Split multiple statements on one line in src/foo.py:42")
- **And** `FixPlan.affected_files` SHALL contain `src/foo.py`

#### Scenario: AssertionError produces specific root cause

- **Given** a failure detail containing `AssertionError` and a test name
- **And** all probes return `confirmed=False`
- **When** `targeted_fix()` is called
- **Then** the returned `FixPlan.root_cause` SHALL describe a test expectation mismatch
- **And** `FixPlan.fix_description` SHALL include the test name or assertion context

### Requirement: Fallback Hypotheses SHALL Reflect Failure Context

The generic fallback hypotheses ("Recent code change introduced a regression", "Missing or incorrect configuration", "Environment or dependency issue") MUST be replaced or augmented with hypotheses derived from the actual failure detail text when available.

#### Scenario: Unknown error pattern still produces actionable hypothesis

- **Given** a failure detail that matches none of the `_PATTERNS` entries
- **When** `hypothesize()` is called
- **Then** the lowest-confidence hypothesis MAY be generic, but at least one hypothesis SHALL reference a snippet of the actual failure detail (up to 120 chars) as evidence

#### Scenario: Multiple error patterns produce non-redundant hypotheses

- **Given** a failure detail containing both `ImportError` and `TypeError`
- **When** `hypothesize()` is called
- **Then** the returned hypotheses SHALL contain distinct root-cause descriptions for each matched pattern
- **And** the generic fallback hypotheses ("Recent code change introduced a regression") SHALL NOT appear if they would displace a more specific matched hypothesis

### Requirement: FixPlan SHALL Include Actionable Repair Hint

Every `FixPlan` returned by `targeted_fix()` MUST include a repair hint that is actionable (file path, line number, or code change suggestion) whenever the evidence contains extractable location information.

#### Scenario: Evidence contains file path and line number

- **Given** hypothesis evidence like `"error in src/bar.py:108: undefined name 'baz'"`
- **When** `targeted_fix()` generates a `FixPlan`
- **Then** `FixPlan.affected_files` SHALL include `src/bar.py`
- **And** `FixPlan.fix_description` SHALL reference line 108 or the symbol `baz`
