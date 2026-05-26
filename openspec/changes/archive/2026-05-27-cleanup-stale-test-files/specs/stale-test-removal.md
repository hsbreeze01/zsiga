# Spec: Stale Test File Removal

## REMOVED Requirements

### Requirement: Remove all stale test_spec_* files

The `tests/` directory SHALL contain zero files matching the `test_spec_*` glob pattern
after cleanup. All such files belong to proposals that have been archived or deleted
and no longer have corresponding source code in the project.

#### Scenario: No test_spec_* files remain after cleanup

- **testable**: true
- **target**: tests/test_spec_cleanup_stale_test_files__stale_test_removal.py
- **Given** the `tests/` directory may contain files matching `test_spec_*.py`
- **When** the cleanup is applied
- **Then** `Path("tests/").glob("test_spec_*.py")` SHALL yield zero results

#### Scenario: Non-spec test files are preserved

- **testable**: true
- **target**: tests/test_spec_cleanup_stale_test_files__stale_test_removal.py
- **Given** the `tests/` directory contains non-spec test files (e.g. `test_ast_tools.py`,
  `test_compaction.py`, `test_config_diff.py`, `test_config_validation.py`,
  `test_daemon_cycle_resilience.py`, `test_git_ops.py`, `test_logging.py`,
  `test_spec_parser.py`, `test_venv_usage.py`)
- **When** the cleanup is applied
- **Then** each of these files SHALL still exist and SHALL be byte-identical to
  their pre-cleanup content (no modification, no truncation)

#### Scenario: conftest_zsiga.py is preserved

- **testable**: true
- **target**: tests/test_spec_cleanup_stale_test_files__stale_test_removal.py
- **Given** `tests/conftest_zsiga.py` exists
- **When** the cleanup is applied
- **Then** `tests/conftest_zsiga.py` SHALL still exist and be byte-identical to its
  pre-cleanup content

#### Scenario: Deleted files are recoverable from git history

- **testable**: true
- **target**: tests/test_spec_cleanup_stale_test_files__stale_test_removal.py
- **Given** the cleanup has deleted one or more `test_spec_*` files
- **When** `git log --diff-filter=D --name-only -- tests/test_spec_*.py` is run
- **Then** git SHALL report those files as deleted, confirming they can be restored
  via `git checkout`

#### Scenario: Remaining test suite passes after cleanup

- **testable**: false
- **Given** all `test_spec_*` files have been removed
- **When** `pytest tests/ -x` is executed
- **Then** the test run SHALL complete with exit code 0 (all collected tests pass,
  no import errors, no fixture resolution failures)

### Requirement: No source code or configuration changes

The cleanup SHALL NOT modify any file outside the `tests/` directory.
Specifically, files under `skills/`, `site/`, `pyproject.toml`, and
`requirements.txt` MUST remain byte-identical to their pre-cleanup state.

#### Scenario: No files outside tests/ are modified

- **testable**: true
- **target**: tests/test_spec_cleanup_stale_test_files__stale_test_removal.py
- **Given** the cleanup is applied
- **When** `git diff --name-only` is inspected
- **Then** every changed path SHALL start with `tests/`
