# transport-factory.md

## ADDED Requirements

### Requirement: create_transport Factory Function

`create_transport(target_config)` SHALL return a `LocalTransport` when
`target_config` has no `ssh` attribute or when `ssh` is falsy. It SHALL return
an `SSHTransport` when `target_config.ssh` is truthy, passing `ssh.host`,
`ssh.user`, `ssh.port`, and `ssh.key_path` to the `SSHTransport` constructor.

#### Scenario: create_transport returns LocalTransport when no ssh attribute

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result MUST be an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result MUST be an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport when ssh is truthy

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with a truthy `ssh` attribute having
    `host="myhost"`, `user="deploy"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result MUST be an instance of `SSHTransport` with matching
    `host`, `user`, `port`, and `key_path`
