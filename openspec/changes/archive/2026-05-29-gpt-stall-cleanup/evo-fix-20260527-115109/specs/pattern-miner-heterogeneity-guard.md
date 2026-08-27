# pattern-miner-heterogeneity-guard

## ADDED Requirements

### Requirement: Pattern heterogeneity detection

The pattern miner SHALL detect when a `pattern_key` groups failures that have fundamentally
different root causes (heterogeneous group) and mark such patterns with a `do_not_fix` flag.

#### Scenario: Homogeneous pattern remains fixable

- **testable**: true
- **target**: zsiga/memory/pattern_miner.py::mine_patterns
- **Given** learnings.jsonl contains 4 entries with pattern_key `"proposal_gate.reject"` where all entries have the same takeaway prefix
- **When** `mine_patterns(min_occurrences=3)` is called
- **Then** the returned Pattern for `"proposal_gate.reject"` SHALL have `do_not_fix` set to `False`

#### Scenario: Heterogeneous pattern marked as do_not_fix

- **testable**: true
- **target**: zsiga/memory/pattern_miner.py::mine_patterns
- **Given** learnings.jsonl contains 5 entries with pattern_key `"pipeline.fail.verify.diagnosed"` where entries have different `error_domain` values (`"code"`, `"infrastructure"`, `"pipeline"`)
- **When** `mine_patterns(min_occurrences=3)` is called
- **Then** the returned Pattern for `"pipeline.fail.verify.diagnosed"` SHALL have `do_not_fix` set to `True`

#### Scenario: Heterogeneity check uses error_domain diversity

- **testable**: true
- **target**: zsiga/memory/pattern_miner.py::_is_heterogeneous
- **Given** a list of 5 learning records with the same pattern_key but 3 distinct `error_domain` values
- **When** `_is_heterogeneous(records)` is called
- **Then** it SHALL return `True`

### Requirement: do_not_fix flag in Pattern dataclass

The `Pattern` dataclass SHALL include a `do_not_fix` boolean field defaulting to `False`.

#### Scenario: Pattern dataclass has do_not_fix field

- **testable**: true
- **target**: zsiga/memory/pattern_miner.py::Pattern
- **Given** the Pattern dataclass definition
- **When** a Pattern instance is created with only `key="test", count=1, severity="low"`
- **Then** the instance's `do_not_fix` attribute SHALL be `False`

### Requirement: Generate warnings include do_not_fix status

When `generate_warnings` produces text, patterns marked `do_not_fix=True` SHALL include
a `[DO NOT FIX]` prefix in the warning line.

#### Scenario: Warning for do_not_fix pattern includes marker

- **testable**: true
- **target**: zsiga/memory/pattern_miner.py::generate_warnings
- **Given** a list containing one Pattern with `key="pipeline.fail.verify.diagnosed"`, `count=5`, `severity="high"`, `do_not_fix=True`
- **When** `generate_warnings(patterns)` is called
- **Then** the output text SHALL contain `[DO NOT FIX]`
