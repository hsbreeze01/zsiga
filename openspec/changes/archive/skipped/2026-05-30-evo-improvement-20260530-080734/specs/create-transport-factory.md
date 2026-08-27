# create-transport-factory

## ADDED Requirements

### Requirement: create_transport returns correct transport type

`create_transport(target_config)` SHALL return `LocalTransport` when `target_config.ssh` is `None` or missing. It SHALL return `SSHTransport` when `target_config.ssh` is a namespace with `host`, `user`, `port`, `key_path` attributes.

#### Scenario: returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `SimpleNamespace(ssh=None)` config
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: returns LocalTransport when ssh attribute is missing

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `SimpleNamespace()` config (no ssh attribute)
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: returns SSHTransport when ssh config is present

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config with `ssh=SimpleNamespace(host="myhost", user="ubuntu", port=2222, key_path="/key")`
- **When** `create_transport(config)` is called
- **Then** the result is an `SSHTransport` with matching `host`, `user`, `port`, and `key_path`
