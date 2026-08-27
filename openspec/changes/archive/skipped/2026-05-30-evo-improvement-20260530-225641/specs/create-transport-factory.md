# create-transport-factory

## ADDED Requirements

### Requirement: create_transport returns LocalTransport for local config

When the `target_config` has no `ssh` attribute or `ssh` is `None`/falsy,
`create_transport` SHALL return a `LocalTransport` instance.

#### Scenario: create_transport returns LocalTransport without ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `TargetConfig` with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

### Requirement: create_transport returns SSHTransport for ssh config

When the `target_config` has a truthy `ssh` attribute with `host`, `user`,
`port`, `key_path`, `create_transport` SHALL return an `SSHTransport` instance
constructed with those parameters.

#### Scenario: create_transport returns SSHTransport with ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `TargetConfig` with `ssh=SSHConfig(host="myhost", user="bob", port=2222, key_path="/key")`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an `SSHTransport` instance with `host="myhost"`,
  `user="bob"`, `port=2222`, `key_path="/key"`

#### Scenario: create_transport with ssh no user or key

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `TargetConfig` with `ssh=SSHConfig(host="myhost")`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an `SSHTransport` instance with `host="myhost"`,
  `user=None`, `port=22`, `key_path=None`
