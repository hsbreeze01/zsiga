# create-transport-factory

## ADDED Requirements

### Requirement: create_transport factory function tests

`tests/test_transport.py` SHALL contain a `TestCreateTransport` test class (including a
`test_create_transport` function) that verifies the factory function:

- When `target_config.ssh` is falsy (`None`), returns a `LocalTransport` instance.
- When `target_config.ssh` is truthy, returns an `SSHTransport` instance with attributes
  derived from `ssh.host`, `ssh.user`, `ssh.port`, `ssh.key_path`.

#### Scenario: create_transport returns LocalTransport when no ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` namespace with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport when ssh config present

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` namespace with `ssh` having `host="h", user="u", port=22, key_path=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `SSHTransport` with `.host == "h"` and `.user == "u"`

#### Scenario: create_transport returns SSHTransport with non-default port

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` namespace with `ssh` having `host="h", user="u", port=2222, key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `SSHTransport` with `.port == 2222` and `.key_path == "/key"`

---

### Requirement: test file passes pytest and lint

`tests/test_transport.py` SHALL pass:
- `python -m pytest tests/test_transport.py` with exit code 0
- `ruff check tests/test_transport.py` with no errors

#### Scenario: pytest passes on test_transport.py

- **testable**: true
- **target**: tests/test_transport.py
- **Given** the file `tests/test_transport.py` exists
- **When** `python -m pytest tests/test_transport.py` is executed
- **Then** the exit code is 0

#### Scenario: ruff check passes on test_transport.py

- **testable**: true
- **target**: tests/test_transport.py
- **Given** the file `tests/test_transport.py` exists
- **When** `ruff check tests/test_transport.py` is executed
- **Then** the exit code is 0
