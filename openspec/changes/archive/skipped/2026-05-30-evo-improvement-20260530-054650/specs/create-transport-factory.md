# create-transport-factory

## ADDED Requirements

### REQ-FACTORY-001: create_transport SHALL return LocalTransport when no SSH config

When `target_config` has no `ssh` attribute or `ssh` is falsy/None,
the factory MUST return a `LocalTransport` instance.

#### Scenario: create_transport returns LocalTransport when ssh attribute is missing

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `target_config` object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `target_config` object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

---

### REQ-FACTORY-002: create_transport SHALL return SSHTransport when SSH config present

When `target_config.ssh` is a truthy object with `host`, `user`,
`port`, `key_path`, the factory MUST return a properly configured
`SSHTransport`.

#### Scenario: create_transport returns SSHTransport with correct attributes

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `target_config` with `ssh` having `host="srv"`, `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an `SSHTransport` instance with `host="srv"`, `user="alice"`, `port=2222`, `key_path="/key"`
