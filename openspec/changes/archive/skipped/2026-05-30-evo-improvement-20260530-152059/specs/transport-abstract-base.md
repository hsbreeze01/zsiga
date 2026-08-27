# transport-abstract-base

## ADDED Requirements

### Requirement: Transport ABC enforces subclass contract

`Transport` SHALL be an abstract base class that defines the interface contract
for all transport implementations. Direct use of `Transport.run_shell` MUST raise
`NotImplementedError`. `Transport.close` SHALL be a safe no-op (no exception).

#### Scenario: Direct call to Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Direct call to Transport.close succeeds without error

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the call returns `None`
