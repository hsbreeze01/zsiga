# Delta Spec: Lint Cleanup

## MODIFIED Requirements

### REQ-LINT-001: Source code SHALL pass ruff check with zero errors

The `zsiga/` source tree SHALL produce zero errors when scanned by `ruff check zsiga/`.

#### Scenario: Unused imports are removed
- **Given** a Python module in `zsiga/` contains an import statement that is never referenced in the module
- **When** `ruff check` is executed against the module
- **Then** the import SHALL be removed so that no F401 diagnostic remains

#### Scenario: F-strings without placeholders are converted to plain strings
- **Given** an f-string literal in `zsiga/` contains no `{...}` interpolation expressions
- **When** `ruff check` is executed against the module
- **Then** the f-string SHALL be converted to a regular string literal so that no F541 diagnostic remains

#### Scenario: Unused local variables are eliminated
- **Given** a local variable is assigned in `zsiga/` but never read before going out of scope
- **When** `ruff check` is executed against the module
- **Then** the unused assignment SHALL be removed or the variable SHALL be consumed so that no F841 diagnostic remains

### REQ-LINT-002: LSP tools SHALL be used to validate each lint finding before fixing

Before modifying any source line, the agent SHALL use `diagnostics` to identify issues, then `goto_definition` or `find_references` to confirm that the flagged symbol is truly unreferenced (ruling out dynamic/convention-based usage).

#### Scenario: Unused import verified via find_references
- **Given** `diagnostics` reports F401 for an import in a module
- **When** the agent invokes `find_references` on the imported name
- **Then** the agent SHALL only remove the import if no references are found outside the import statement itself

#### Scenario: Unused variable verified via find_references
- **Given** `diagnostics` reports F841 for a local variable
- **When** the agent invokes `find_references` on the variable
- **Then** the agent SHALL only remove the assignment if the variable is confirmed unused

### REQ-LINT-003: Existing tests SHALL continue to pass after lint fixes

All tests under `tests/` SHALL pass without modification after the lint cleanup is applied.

#### Scenario: Test suite passes post-cleanup
- **Given** all lint fixes have been applied to `zsiga/`
- **When** `pytest tests/` is executed
- **Then** all tests SHALL pass with no regressions
