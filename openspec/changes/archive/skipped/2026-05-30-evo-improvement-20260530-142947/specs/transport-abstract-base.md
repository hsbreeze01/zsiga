# spec: transport-abstract-base

## ADDED Requirements

### Requirement: Transport base class defines interface contract

`Transport` SHALL define `run_shell(cmd, cwd, timeout, stdin_data)` and `close()` as part of its public interface. Calling `Transport().run_shell(...)` MUST raise `NotImplementedError`. Calling `Transport().close()` MUST return `None`.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a bare `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` SHALL be raised

#### Scenario: Transport.close returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close
- **Given** a bare `Transport` instance
- **When** `close()` is called
- **Then** the return value SHALL be `None`

