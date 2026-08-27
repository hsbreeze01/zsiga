# daemon-pipeline-builders

## ADDED Requirements

### Requirement: _build_pipeline_status returns structured output for no active proposal

When no active proposal exists, `_build_pipeline_status()` SHALL return a dict
with default structure containing `active_proposal` as `None`, an empty
`phase_progress` list, and daemon state from `_read_daemon_state()`.

#### Scenario: Returns default structure when no changes directory

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `base_path` points to a directory with no `openspec/changes/` subdirectory
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** the result dict has `active_proposal` equal to `None`, `queue` is a list, and `phase_progress` is a list

#### Scenario: Includes queue entries for proposal directories

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `base_path` contains `openspec/changes/my-proposal/proposal.md`
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** the result's `queue` list contains at least one entry with `name` equal to `"my-proposal"`

#### Scenario: Daemon sub-dict contains state and cycle from daemon_state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state()` returns `{"state": "running", "cycle": 7}`
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** the result's `daemon` sub-dict has `"state"` equal to `"running"` and `"cycle"` equal to `7`

### Requirement: _build_proposal_detail reads files and returns structured output

`_build_proposal_detail()` SHALL return a dict containing `proposal_name`,
`files`, `phases`, and `phase_state`. When the proposal directory does not
exist, it SHALL include an `error` key.

#### Scenario: Returns error for non-existent proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` contains no directory matching the proposal name in `openspec/changes/` or its `archive/`
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent-proposal")` is called
- **Then** the result contains key `"error"` with a string value mentioning the proposal name

#### Scenario: Reads proposal.md content into files dict

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/my-proposal/proposal.md` exists with content `# My Proposal`
- **When** `_build_proposal_detail(":memory:", base_path, "my-proposal")` is called
- **Then** the result's `files` dict contains key `"proposal.md"` with value starting with `# My Proposal`

#### Scenario: Reads phase_state when .phase_state file exists

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/my-proposal/.phase_state` exists containing `{"current_phase": "IMPLEMENT"}`
- **When** `_build_proposal_detail(":memory:", base_path, "my-proposal")` is called
- **Then** the result's `phase_state` is a dict with `"current_phase"` equal to `"IMPLEMENT"`

### Requirement: _health_check probes database liveness

`_health_check()` SHALL return a dict with `status` key set to `"healthy"` when
the database is reachable and `"unhealthy"` when it is not.

#### Scenario: Returns healthy for accessible database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a valid SQLite database with a `changes` table
- **When** `_health_check(db_path)` is called
- **Then** the result has `status` equal to `"healthy"` and `db_records` is an integer

#### Scenario: Returns unhealthy for missing database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a non-existent database file path
- **When** `_health_check("/nonexistent/path.db")` is called
- **Then** the result has `status` equal to `"unhealthy"` and `error` is a string

### Requirement: _build_evolution_status returns structured config state

`_build_evolution_status()` SHALL return a dict with `enabled`, `window`,
`state`, and `paused` keys reflecting the evolution engine configuration.

#### Scenario: Returns enabled=false and paused=false with default config

- **testable**: false
- **Given** `zsiga.yaml` with `evolution_enabled: false`
- **When** `_build_evolution_status(base_path)` is called
- **Then** the result has `enabled` equal to `False` and `paused` equal to `False`

> Note: This scenario requires mocking `zsiga.config.load_config` and
> `zsiga.intake.evolution.EvolutionEngine` with complex internal state.
> The mock chain depth makes this unsuitable for mechanical verification
> and it SHOULD be covered via integration testing.
