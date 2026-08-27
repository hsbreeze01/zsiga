# create-transport-factory

## ADDED Requirements

### REQ-FACT-001: Transport factory selection

`create_transport(target_config)` SHALL return a `LocalTransport` instance when `target_config` has no `ssh` attribute or when `target_config.ssh` is `None` or falsy. It SHALL return an `SSHTransport` instance when `target_config.ssh` is truthy, passing `ssh.host`, `ssh.user`, `ssh.port`, and `ssh.key_path` as constructor arguments.

#### Scenario: create_transport returns LocalTransport without ssh attribute

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport with ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` with `ssh=SimpleNamespace(host="myhost", user="admin", port=2222, key_path="/key")`
- **When** `create_transport(target_config)` is called
- **Then** the result is an `SSHTransport` instance with `host="myhost"`, `user="admin"`, `port=2222`, `key_path="/key"`
