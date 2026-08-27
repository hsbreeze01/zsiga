# transport-abstract-base

## ADDED Requirements

### Requirement: Transport.run_shell SHALL raise NotImplementedError

`Transport` is the abstract base class for all transport backends. Its
`run_shell` method SHALL raise `NotImplementedError` when called directly,
forcing subclasses to provide a concrete implementation.

#### Scenario: calling run_shell on base Transport raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** `NotImplementedError` SHALL be raised

#### Scenario: calling close on base Transport returns without error

- **testable**: true
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception SHALL be raised
