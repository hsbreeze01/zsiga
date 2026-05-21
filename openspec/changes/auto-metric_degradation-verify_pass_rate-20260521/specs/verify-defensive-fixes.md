# Spec: Verify Defensive Fixes

## ADDED Requirements

### Requirement: Pre-verify lint checkpoint

The verify phase SHALL execute a lint pre-check using `ruff check` on all changed files before running pytest. If the lint pre-check fails, the verify phase SHALL fail immediately with a categorized `lint` failure, skipping pytest execution.

#### Scenario: Lint error detected before tests

- **Given** a change introduces a file with a ruff violation (e.g., unused import, line too long)
- **When** the verify phase begins
- **Then** ruff check SHALL be executed on the changed files first
- **And** if ruff reports errors, the verify phase SHALL fail with category `lint`
- **And** pytest SHALL NOT be executed

#### Scenario: Lint passes, tests run

- **Given** all changed files pass ruff check
- **When** the verify phase begins
- **Then** ruff check SHALL pass
- **And** the verify phase SHALL proceed to pytest execution

### Requirement: Dependency integrity pre-check

The verify phase SHALL validate that all Python modules imported by changed files are resolvable before running tests. If any import cannot be resolved, the verify phase SHALL fail with a categorized `dependency` failure.

#### Scenario: Missing import detected

- **Given** a changed file contains `from foo.bar import baz` where `foo.bar` is not installed or does not exist
- **When** the verify phase performs dependency pre-check
- **Then** the verify phase SHALL fail with category `dependency`
- **And** the failure message SHALL include the unresolvable module name

#### Scenario: All imports resolvable

- **Given** all imports in changed files resolve successfully
- **When** the verify phase performs dependency pre-check
- **Then** the pre-check SHALL pass
- **And** the verify phase SHALL proceed to the next checkpoint

### Requirement: Regression detection via test baseline snapshot

The verify phase SHALL maintain a snapshot of the set of tests that passed in the previous successful verify run. When a new verify run completes, any test that transitions from pass to fail SHALL be flagged as a `regression` failure.

#### Scenario: Previously passing test now fails

- **Given** test `test_foo` passed in the last successful verify run (recorded in baseline snapshot)
- **And** test `test_foo` fails in the current verify run
- **When** the verify phase evaluates results against the baseline
- **Then** the failure SHALL be categorized as `regression`
- **And** the regression SHALL be reported with both the previous passing and current failing status

#### Scenario: New test fails (not a regression)

- **Given** test `test_bar` does not exist in the baseline snapshot
- **And** test `test_bar` fails in the current verify run
- **When** the verify phase evaluates results against the baseline
- **Then** the failure SHALL be categorized as `test` (not `regression`)

#### Scenario: Baseline snapshot updated after successful run

- **Given** the verify phase completes with all tests passing
- **When** the baseline snapshot is updated
- **Then** the snapshot SHALL contain the complete set of passing test names for comparison in the next run

## MODIFIED Requirements

### Requirement: Verify phase execution order

The verify phase SHALL execute checkpoints in the following strict order:
1. Lint pre-check (ruff)
2. Dependency integrity pre-check
3. Test execution (pytest)
4. Regression detection (baseline comparison)

Each checkpoint that fails SHALL short-circuit the remaining checkpoints.

#### Scenario: All checkpoints pass sequentially

- **Given** changed files have no lint errors, all imports resolve, and all tests pass
- **When** the verify phase runs
- **Then** each checkpoint SHALL execute in order (lint → dependency → test → regression)
- **And** the verify phase SHALL report overall success
