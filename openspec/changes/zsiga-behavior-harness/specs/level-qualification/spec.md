## ADDED Requirements

### Requirement: Level qualification test suite
The system SHALL provide a qualification test suite per level that validates behavioral capabilities beyond quantitative metrics. Level upgrade SHALL require both quantitative threshold AND qualification suite pass.

#### Scenario: L5 qualification requires end-to-end implementation
- **WHEN** L5 qualification runs
- **THEN** a test SHALL submit a real proposal through the full pipeline (ENRICH→IMPLEMENT→VERIFY→DELIVER) and verify completion

#### Scenario: L5 qualification requires intent accuracy
- **WHEN** L5 qualification runs
- **THEN** the intent router SHALL achieve >= 90% accuracy on the full INTENT_CASES test set

#### Scenario: L5 qualification requires correct routing for all intent types
- **WHEN** L5 qualification runs
- **THEN** all 6 intent types SHALL route to the correct execution path

#### Scenario: L5 qualification requires recovery capability
- **WHEN** L5 qualification runs
- **THEN** a test SHALL verify that lint failure triggers fix loop and revert-on-exhaustion works

#### Scenario: L5 qualification requires budget phase isolation
- **WHEN** L5 qualification runs
- **THEN** a test SHALL verify set_phase resets budget._used to 0

### Requirement: Qualification result as level gate
The system SHALL use qualification results as a gate for level milestone recording. Quantitative metrics alone SHALL NOT be sufficient.

#### Scenario: Quantitative pass but qualification fail
- **WHEN** quantitative metrics meet threshold (e.g. 80 changes, 85% rate) but qualification tests fail
- **THEN** the level SHALL NOT be marked as achieved

#### Scenario: Both pass
- **WHEN** both quantitative metrics and qualification tests pass
- **THEN** the level snapshot SHALL be recorded with qualification results attached

### Requirement: Qualification result persistence
The system SHALL store qualification results alongside level snapshots for auditability.

#### Scenario: Qualification attached to level snapshot
- **WHEN** a level is achieved after passing qualification
- **THEN** the level_snapshots entry SHALL include a `qualification_results` JSON field with pass/fail per test

### Requirement: CLI qualification command
The system SHALL provide `zsiga harness qualify --level L5` CLI command.

#### Scenario: Manual qualification run
- **WHEN** user runs `zsiga harness qualify --level L5`
- **THEN** the L5 qualification suite SHALL run and print pass/fail per requirement to stdout
