# create-transport-factory.md

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no SSH config

`create_transport(target_config)` SHALL return a `LocalTransport` instance when
`target_config.ssh` is `None` or falsy.

#### Scenario: ssh is None returns LocalTransport

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a mock `target_config` with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

### Requirement: create_transport returns SSHTransport when SSH config present

`create_transport(target_config)` SHALL return an `SSHTransport` instance
initialized with `ssh.host`, `ssh.user`, `ssh.port`, `ssh.key_path` when
`target_config.ssh` is truthy.

#### Scenario: ssh config present returns SSHTransport

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a mock `target_config` with `ssh` having `host="myhost"`,
  `user="alice"`, `port=2222`, `key_path=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `SSHTransport` with `host="myhost"` and
  `port=2222`

#### Scenario: ssh config with missing attribute uses getattr default

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a plain object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`
