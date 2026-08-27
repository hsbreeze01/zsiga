# create-transport-factory

## ADDED Requirements

### Requirement: create_transport returns correct Transport subclass

`create_transport(target_config)` SHALL inspect `target_config` for an `ssh`
attribute. If `ssh` is falsy or absent, it MUST return a `LocalTransport`
instance. If `ssh` is truthy, it MUST return an `SSHTransport` instance
constructed with `ssh.host`, `ssh.user`, `ssh.port`, and `ssh.key_path`.
All returned objects SHALL be instances of the `Transport` base class.

#### Scenario: create_transport returns LocalTransport when no ssh attribute

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `target_config` object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `target_config` object with `ssh = None`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport when ssh is present

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `target_config` object with an `ssh` attribute having
  `host="myhost"`, `user="bob"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `SSHTransport` with matching
  connection parameters

#### Scenario: returned objects are Transport subclass instances

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** both a target_config without `ssh` and one with `ssh`
- **When** `create_transport` is called with each
- **Then** both results SHALL be instances of `Transport`
