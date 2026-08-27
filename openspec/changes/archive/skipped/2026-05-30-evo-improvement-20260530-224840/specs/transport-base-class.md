# transport-base-class.md

## ADDED Requirements

### Requirement: Transport.run_shell raises NotImplementedError

The `Transport` base class SHALL raise `NotImplementedError` when `run_shell` is invoked.
Subclasses MUST override this method to provide concrete behaviour.

#### Scenario: base class run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance
- **When** `run_shell("ls")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: base class close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the call returns `None`
