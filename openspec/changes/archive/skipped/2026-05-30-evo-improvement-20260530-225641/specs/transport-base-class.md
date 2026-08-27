# transport-base-class

## ADDED Requirements

### Requirement: Transport base class abstract contract

The `Transport` base class SHALL define the interface contract for all transport
implementations.  The `run_shell` method MUST raise `NotImplementedError` when
called directly.  The `close` method SHALL be a no-op (return `None`).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** it SHALL raise `NotImplementedError`

#### Scenario: Transport.close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` without error
