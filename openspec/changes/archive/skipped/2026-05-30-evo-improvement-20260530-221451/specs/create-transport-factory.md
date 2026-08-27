# create-transport-factory

## ADDED Requirements

### Requirement: create_transport dispatches by SSH config presence

`create_transport(target_config)` SHALL return a `LocalTransport` when the
`target_config` has no `ssh` attribute or when `ssh` is `None`/falsy. It SHALL
return an `SSHTransport` when `ssh` is a config object with `host`, `user`,
`port`, and `key_path` attributes, forwarding those values to the
`SSHTransport` constructor.

#### Scenario: returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: returns LocalTransport when ssh attribute is missing

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: returns SSHTransport when ssh config is present

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a config object whose `ssh` attribute has
  `host="myhost"`, `user="ubuntu"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an `SSHTransport` instance with
  `host="myhost"`, `user="ubuntu"`, `port=2222`, `key_path="/key"`
