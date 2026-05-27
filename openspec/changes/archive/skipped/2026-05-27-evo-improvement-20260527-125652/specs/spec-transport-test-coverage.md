# Spec: Transport Module Test Coverage

## ADDED Requirements

### Requirement: Test file tests/test_transport.py SHALL exist and cover core symbols

A new test file `tests/test_transport.py` MUST be created covering
`create_transport`, `LocalTransport`, `SSHTransport`, and the base `Transport`
class. Each test function SHALL use real assertions against the actual module
API — no pass/placeholder patterns.

#### Scenario: test-transport-file-exists

- **testable**: true
- **target**: tests/test_transport.py

- **Given** the project root directory
- **When** the filesystem is checked for tests/test_transport.py
- **Then** the file SHALL exist

#### Scenario: test-transport-file-imports-core-symbols

- **testable**: true
- **target**: tests/test_transport.py

- **Given** the content of tests/test_transport.py
- **When** the file is scanned for import statements
- **Then** it SHALL contain an import of create_transport or LocalTransport or
  SSHTransport from zsiga.transport

#### Scenario: create-transport-returns-local-when-no-ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a config-like object whose ssh attribute is None
- **When** create_transport is called with that config
- **Then** the returned object SHALL be an instance of LocalTransport

#### Scenario: create-transport-returns-ssh-when-ssh-config-present

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a config-like object whose ssh attribute has host="myhost",
  user="u", port=2222, key_path="/key"
- **When** create_transport is called with that config
- **Then** the returned object SHALL be an instance of SSHTransport with
  host=="myhost", user=="u", port==2222, key_path=="/key"

#### Scenario: ssh-transport-expands-tilde-in-key-path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** an SSHTransport constructed with key_path="~/mykey"
- **When** the key_path attribute is inspected
- **Then** it SHALL NOT start with "~" and SHALL contain the expanded home
  directory path

#### Scenario: ssh-transport-target-includes-user-when-set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** an SSHTransport with host="server" and user="alice"
- **When** _target() is called
- **Then** it SHALL return "alice@server"

#### Scenario: ssh-transport-target-returns-bare-host-when-no-user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** an SSHTransport with host="server" and user=None
- **When** _target() is called
- **Then** it SHALL return "server"

#### Scenario: transport-base-class-run-shell-raises-not-implemented

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a Transport base class instance
- **When** run_shell is called
- **Then** it SHALL raise NotImplementedError

#### Scenario: transport-base-class-close-does-not-raise

- **testable**: true
- **target**: zsiga/transport.py::Transport.close

- **Given** a Transport base class instance
- **When** close() is called
- **Then** no exception SHALL be raised

#### Scenario: ssh-transport-base-args-includes-custom-port

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** an SSHTransport with host="s", port=2222, key_path=None
- **When** _base_args() is called
- **Then** the returned list SHALL contain "-p" followed by "2222"

#### Scenario: ssh-transport-base-args-includes-identity-file

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** an SSHTransport with host="s", port=22, key_path="/home/user/.ssh/id_rsa"
- **When** _base_args() is called
- **Then** the returned list SHALL contain "-i" followed by "/home/user/.ssh/id_rsa"
