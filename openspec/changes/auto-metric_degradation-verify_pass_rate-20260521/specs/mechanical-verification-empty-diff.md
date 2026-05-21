# Spec: Mechanical Verification Empty-Diff Handling

## MODIFIED Requirements

### Requirement: verify_mechanical with since_sha and no changed files SHALL pass cleanly

**Existing behavior**: When `_get_changed_files` returns an empty list, `verify_mechanical` skips lint but still runs `pytest` on an empty `test_targets` list — which may invoke the bare test command with no arguments, potentially running the full suite unnecessarily or producing unexpected exit codes.

**Modified behavior**: When both `changed` (changed source files) and `test_targets` (related test files) are empty, `verify_mechanical` SHALL return `(True, "")` immediately without invoking any lint or test commands.

#### Scenario: Empty diff between pre-impl SHA and HEAD
- **Given** `since_sha` is set and `_get_changed_files` returns `[]`
- **And** `_get_test_targets` also returns `[]`
- **When** `verify_mechanical` is called
- **Then** it SHALL return `(True, "")` without running `ruff` or `pytest`

#### Scenario: Only test files changed (no source files)
- **Given** `_get_changed_files` returns `["tests/test_foo.py"]` (only test files, no source)
- **And** `_get_test_targets` returns `["tests/test_foo.py"]`
- **When** `verify_mechanical` is called
- **Then** it SHALL skip lint (no `.py` source files in changed list outside `tests/`)
- **And** it SHALL run pytest on `["tests/test_foo.py"]`

### Requirement: _get_changed_files SHALL exclude site-packages paths consistently

**Existing behavior**: `_get_changed_files` filters out paths containing `/site-packages/`.

**Modified behavior**: The filter SHALL also exclude any path matching `**/site-packages/**` (with glob-style matching) and SHALL exclude paths under `venv*/` and `.venv/` directories. This prevents false positives when pip install operations create files in the venv that appear in the diff.

#### Scenario: Venv file appears in diff after pip install
- **Given** `git diff --name-only` includes `venv2/lib/python3.9/site-packages/new_package/__init__.py`
- **When** `_get_changed_files` processes the result
- **Then** that file SHALL be excluded from the returned list
