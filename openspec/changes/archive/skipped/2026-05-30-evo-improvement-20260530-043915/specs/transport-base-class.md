# Transport Base Class Test Coverage

## ADDED Requirements

### Requirement: Transport base class behavior

`Transport` SHALL be an abstract base class whose `run_shell()` method raises `NotImplementedError` when called directly, and whose `close()` method SHALL be a no-op (return `None`).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** it SHALL raise `NotImplementedError`

#### Scenario: Transport.close is a no-op

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` without raising

