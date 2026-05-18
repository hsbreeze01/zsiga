# Delta Spec: File Change Impact Analyzer

## ADDED Requirements

### Requirement: Import Graph Construction

The system SHALL build a directed import graph for all Python source files in the target project, excluding `venv/`, `__pycache__/`, and `site-packages/` directories.

#### Scenario: Build graph from project with standard imports

- **Given** a target project at `/path/to/project`
- **When** the import graph is constructed
- **Then** the graph SHALL contain one node per `.py` file (using relative path from project root)
- **And** each node SHALL have directed edges to all files it imports via `import X`, `from X import Y`, or `from X.Y import Z` statements
- **And** the graph SHALL resolve relative imports (e.g., `from ..utils import foo` resolves to the parent package's `utils.py`)

#### Scenario: Handle missing or unreadable files gracefully

- **Given** a target project where some `.py` files are unreadable or contain syntax errors
- **When** the import graph is constructed
- **Then** those files SHALL be skipped without raising an exception
- **And** the graph SHALL include all successfully parsed files

### Requirement: Downstream Dependency Discovery

The system SHALL compute the set of downstream dependents for a given list of changed files by traversing the reverse import graph.

#### Scenario: Find direct dependents of a changed file

- **Given** file `zsiga/pipeline/utils.py` is in the changed file list
- **And** files `zsiga/pipeline/diagnoser.py` and `zsiga/pipeline/dependency.py` both import from `utils`
- **When** downstream dependencies are computed
- **Then** the result SHALL include `zsiga/pipeline/diagnoser.py` and `zsiga/pipeline/dependency.py`

#### Scenario: Find transitive dependents

- **Given** file `zsiga/transport.py` is changed
- **And** `zsiga/pipeline/utils.py` imports `transport.py`
- **And** `zsiga/pipeline/diagnoser.py` imports `utils.py`
- **When** downstream dependencies are computed
- **Then** the result SHALL include both `zsiga/pipeline/utils.py` AND `zsiga/pipeline/diagnoser.py`

#### Scenario: Changed file with no dependents

- **Given** a changed file that nothing else imports
- **When** downstream dependencies are computed
- **Then** the downstream dependents set SHALL be empty

### Requirement: Test Scope Estimation

The system SHALL identify which test files cover the changed modules by analyzing test file imports and naming conventions.

#### Scenario: Match test files by import reference

- **Given** file `zsiga/pipeline/dependency.py` is in the changed file list
- **And** `tests/test_dependency.py` contains `from zsiga.pipeline.dependency import ...`
- **When** test scope is estimated
- **Then** `tests/test_dependency.py` SHALL be included in the test scope

#### Scenario: Match test files by naming convention fallback

- **Given** file `zsiga/pipeline/impact.py` is in the changed file list
- **And** no test file imports it directly
- **But** `tests/test_impact.py` exists in the project
- **When** test scope is estimated
- **Then** `tests/test_impact.py` SHALL be included in the test scope via naming convention match

#### Scenario: No test coverage detected

- **Given** a changed file with no matching test file by import or naming convention
- **When** test scope is estimated
- **Then** the test scope for that file SHALL be reported as empty

### Requirement: Risk Level Classification

The system SHALL classify the overall risk of a set of changed files as `low`, `medium`, or `high`.

#### Scenario: Low risk — few dependents and test coverage exists

- **Given** a set of changed files whose combined downstream dependent count is ≤ 2
- **And** each changed file has at least one matching test file
- **When** risk is classified
- **Then** the risk level SHALL be `low`

#### Scenario: Medium risk — moderate blast radius or partial coverage

- **Given** a set of changed files whose combined downstream dependent count is between 3 and 5
- **Or** at least one changed file has no matching test file
- **When** risk is classified
- **Then** the risk level SHALL be `medium`

#### Scenario: High risk — wide blast radius or core infrastructure

- **Given** a set of changed files whose combined downstream dependent count is ≥ 6
- **Or** any changed file is a core infrastructure file (transport, config, or pipeline utils)
- **When** risk is classified
- **Then** the risk level SHALL be `high`

### Requirement: Analyze Impact Entry Point

The system SHALL expose an `analyze_impact` function that accepts a list of changed file paths and a target project path, and returns a structured result.

#### Scenario: Full analysis returns structured result

- **Given** a target project at `/path/to/project`
- **And** changed files `["zsiga/pipeline/utils.py", "zsiga/transport.py"]`
- **When** `analyze_impact` is called
- **Then** the result SHALL contain:
  - `changed_files`: the input list
  - `downstream`: a dict mapping each changed file to its downstream dependents
  - `test_scope`: a list of test files that cover the changed modules
  - `risk_level`: one of `"low"`, `"medium"`, `"high"`
  - `summary`: a human-readable string describing the impact

#### Scenario: Empty changed files list

- **Given** an empty list of changed files
- **When** `analyze_impact` is called
- **Then** the result SHALL have empty `downstream`, empty `test_scope`, `risk_level` of `"low"`, and a summary stating no changes to analyze

#### Scenario: Non-existent file in changed list

- **Given** a changed file path that does not exist in the project
- **When** `analyze_impact` is called
- **Then** that file SHALL be included in `changed_files` but have an empty downstream list
- **And** it SHALL NOT cause an error
