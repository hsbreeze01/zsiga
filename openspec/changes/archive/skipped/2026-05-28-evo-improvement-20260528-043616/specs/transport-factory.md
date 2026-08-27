# transport-factory

## ADDED Requirements

### Requirement: create_transport returns LocalTransport without ssh config

`create_transport(target_config)` SHALL return a `LocalTransport` instance when
`target_config` has no `ssh` attribute or when the `ssh` attribute is falsy.

#### Scenario: create_transport returns LocalTransport without ssh attribute

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport with falsy ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object whose `ssh` attribute is `None`
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

---

### Requirement: create_transport returns SSHTransport with ssh config

When `target_config` has a truthy `ssh` attribute, `create_transport` SHALL
return an `SSHTransport` instance initialised with `ssh.host`, `ssh.user`,
`ssh.port`, and `ssh.key_path`.

#### Scenario: create_transport returns SSHTransport with ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object whose `ssh` attribute has `host="srv"`,
  `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result is an `SSHTransport` instance with `host="srv"`,
  `user="alice"`, `port=2222`

---

### Requirement: create_transport always returns a Transport subclass

Regardless of the config content, the returned object MUST be an instance of
`Transport`.

#### Scenario: LocalTransport result is Transport subclass

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `Transport`

#### Scenario: SSHTransport result is Transport subclass

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with a truthy `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `Transport`
