# create-transport-factory

## ADDED Requirements

### Requirement: create_transport Factory Routing
`create_transport(target_config)` SHALL inspect the `ssh` attribute of
`target_config` (via `getattr`). When `ssh` is `None` or falsy, it MUST return
a `LocalTransport` instance. When `ssh` is a truthy object with `host`, `user`,
`port`, and `key_path` attributes, it MUST return an `SSHTransport` instance
constructed with those attributes.

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the returned instance is of type `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is missing

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute at all
- **When** `create_transport(config)` is called
- **Then** the returned instance is of type `LocalTransport`

#### Scenario: create_transport returns SSHTransport when ssh is configured

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh` attribute having `host="myhost"`,
  `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the returned instance is of type `SSHTransport` with matching
  `host`, `user`, `port`, and `key_path` values
