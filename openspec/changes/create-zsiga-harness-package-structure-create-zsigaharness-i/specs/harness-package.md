# Spec: Harness Package Structure

## ADDED Requirements

### Requirement: Harness package exports
The system SHALL provide a `zsiga.harness` package that re-exports the core public API: `HarnessRunner`, `conftest` fixtures, and result dataclasses.

#### Scenario: Package imports succeed
- Given the `zsiga` package is installed
- When a user writes `from zsiga.harness import HarnessRunner`
- Then the import SHALL succeed without error
- And `HarnessRunner` SHALL be a class

#### Scenario: Conftest fixtures accessible
- Given the `zsiga` package is installed
- When a user writes `from zsiga.harness.conftest import mock_llm_client, mock_transport, temp_git_repo`
- Then all three names SHALL be importable
- And each SHALL be a callable (fixture function)

---

### Requirement: Mock LLM client fixture
The harness SHALL provide a `mock_llm_client` fixture that returns a deterministic, pre-configured mock of the LLM client used by zsiga.

#### Scenario: Mock returns canned responses
- Given the `mock_llm_client` fixture is active
- When any code calls `mock_llm_client.chat(prompt)` (or equivalent interface)
- Then the mock SHALL return a deterministic string response
- And the mock SHALL record all calls for later assertion

#### Scenario: Mock response configurable
- Given the `mock_llm_client` fixture is active
- When a test sets `mock_llm_client.set_response("custom reply")`
- Then subsequent calls to the client SHALL return `"custom reply"`

---

### Requirement: Mock transport fixture
The harness SHALL provide a `mock_transport` fixture that simulates the tool-execution transport layer without real side effects.

#### Scenario: Mock transport records calls
- Given the `mock_transport` fixture is active
- When code invokes `mock_transport.call(tool_name, args)`
- Then the mock SHALL record the `(tool_name, args)` pair
- And SHALL return a configurable default result
- And SHALL NOT perform any real I/O

---

### Requirement: Temp git repo fixture
The harness SHALL provide a `temp_git_repo` fixture that creates an isolated temporary git repository, cleaned up after the test session.

#### Scenario: Fixture provides usable git repo
- Given the `temp_git_repo` fixture is active
- When a test reads `temp_git_repo.path`
- Then it SHALL return a path to a directory containing a valid git repository (with `.git/`)
- And the directory SHALL be writable
- And after the test finishes, the directory SHALL be removed

#### Scenario: Fixture supports initial commit
- Given the `temp_git_repo` fixture is active with `initial_commit=True`
- When the fixture is resolved
- Then the repo SHALL contain at least one commit on the default branch

---

### Requirement: HarnessRunner discovers and runs tests
The `HarnessRunner` class SHALL discover test files within a given directory, execute them, and collect structured results.

#### Scenario: Discover tests in directory
- Given a directory containing test files matching `test_*.py`
- When `HarnessRunner.discover(directory)` is called
- Then it SHALL return a list of test file paths found

#### Scenario: Run discovered tests and collect events
- Given a `HarnessRunner` instance with discovered tests
- When `runner.run()` is called
- Then each test SHALL be executed in an isolated context
- And the runner SHALL emit structured event objects (at minimum: `test_started`, `test_passed`, `test_failed`)
- And `runner.results` SHALL contain a summary with counts of passed/failed/errored tests

#### Scenario: Runner configurable with fixtures
- Given a `HarnessRunner` instance
- When constructed with `fixtures=[mock_llm_client, mock_transport, temp_git_repo]`
- Then those fixtures SHALL be available to all discovered tests during execution
