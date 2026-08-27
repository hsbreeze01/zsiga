# create-transport-factory

## ADDED Requirements

### Requirement: create_transport SHALL return LocalTransport when ssh is absent

When the `target_config` object has no `ssh` attribute or its value is falsy,
`create_transport` SHALL return a `LocalTransport` instance.

#### Scenario: config without ssh returns LocalTransport

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `TargetConfig` with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

### Requirement: create_transport SHALL return SSHTransport when ssh is configured

When the `target_config` object has a truthy `ssh` attribute, `create_transport`
SHALL return an `SSHTransport` instance with `host`, `user`, `port`, `key_path`
forwarded from the `SSHConfig`.

#### Scenario: config with ssh returns SSHTransport with correct params

- **testable**: true
- **target**: zsiga/transport.py::create_transport

- **Given** a `TargetConfig` with `ssh=SSHConfig(host="srv", user="bob", port=2222, key_path="/key")`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `SSHTransport`
- **And** `result.host` SHALL be `"srv"`, `result.user` SHALL be `"bob"`,
  `result.port` SHALL be `2222`, `result.key_path` SHALL be `"/key"`
