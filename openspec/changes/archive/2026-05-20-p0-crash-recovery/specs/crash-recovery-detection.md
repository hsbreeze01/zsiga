# Spec: Crash Recovery Detection

## ADDED Requirements

### REQ-CR-01: Detect Incomplete Changes on Daemon Restart

When the daemon starts a new cycle, it SHALL scan all active changes for incomplete
pipelines — changes that have a `.phase_state` file but no `verify.md` (never reached
successful VERIFY).

#### Scenario: Detect crashed change with stale .phase_state

- **Given** the daemon starts a new cycle
- **And** change `my-change` has `.phase_state` with `current_phase="implement"` and `pre_sha="abc123"`
- **And** `my-change` has no `verify.md` file
- **When** crash recovery detection runs
- **Then** the target project SHALL be rolled back to `pre_sha` via `git reset --hard`
- **And** the `.phase_state` file SHALL be deleted
- **And** the change SHALL be archived
- **And** a lesson SHALL be recorded with `pattern_key="daemon.crash_recovery"`

#### Scenario: No incomplete changes — normal startup

- **Given** the daemon starts a new cycle
- **And** no active changes have `.phase_state` files
- **When** crash recovery detection runs
- **Then** the daemon SHALL proceed normally with no recovery actions

#### Scenario: Change with .phase_state and verify.md — already complete

- **Given** the daemon starts a new cycle
- **And** change `my-change` has `.phase_state` with `current_phase="verify"`
- **And** `my-change` also has `verify.md`
- **When** crash recovery detection runs
- **Then** the change SHALL NOT be treated as crashed
- **And** the `.phase_state` file SHALL be deleted as a cleanup step

### REQ-CR-02: Crash Recovery Timing

Crash recovery detection SHALL run at the beginning of `run_cycle()`,
before any change processing begins.

#### Scenario: Recovery runs before cycle processing

- **Given** there are 3 active changes, one of which is crashed
- **When** `run_cycle()` is called
- **Then** the crashed change SHALL be recovered (rolled back + archived) FIRST
- **And** the remaining 2 changes SHALL be processed normally
