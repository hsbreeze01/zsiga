# Proposal Dedup Blacklist

## ADDED Requirements

### Requirement: `_scan_code_structure` SHALL skip modules whose basename is a known tested alias

After the suffix-matching improvement, a secondary defense SHALL be added:
`_scan_code_structure()` MUST check whether the source module's basename is a
**suffix** of any test file stem.  When the primary exact match fails, the
method SHALL perform a reverse check: for each test file stem, test whether
`stem.endswith("_" + basename)`.  If any test file stem satisfies this
condition, the module is considered tested.

This is the behavioral specification that covers both the primary suffix-match
logic and acts as the dedup mechanism — once the matching is correct, no
`add-tests-*` proposal will be generated for already-tested modules.

#### Scenario: Proposal renderer does not create add-tests-runner when runner.py is matched

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._phase1_intake
- **Given** the real project layout where `zsiga/harness/runner.py` exists and `tests/test_harness_runner.py` exists
- **When** `_scan_code_structure()` is called on the real project
- **Then** the result's `modules_without_tests` list SHALL NOT contain `zsiga/harness/runner.py`

#### Scenario: No add-tests proposal generated for suffix-matched module

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._render_explore_proposal
- **Given** a `_scan_code_structure()` result where `zsiga/harness/runner.py` is NOT in `modules_without_tests`
- **When** `_phase1_intake()` and `_phase2_reflect()` process the findings
- **Then** the `explore_untested` finding SHALL NOT reference `zsiga/harness/runner.py`

