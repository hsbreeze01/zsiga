# create-transport-factory

## ADDED Requirements

### Requirement: create_transport returns correct Transport subclass

`create_transport` SHALL inspect `target_config.ssh`. When `ssh` is falsy
(or missing), it MUST return a `LocalTransport` instance. When `ssh` is present,
it MUST return an `SSHTransport` instance initialized with `ssh.host`,
`ssh.user`, `ssh.port`, and `ssh.key_path`.

#### Scenario: No SSH config returns LocalTransport

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: SSH config present returns SSHTransport

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh` attribute having `host="myhost"`,
      `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `SSHTransport` with `.host="myhost"`,
      `.user="alice"`, `.port=2222`

#### Scenario: SSH config with falsy ssh value returns LocalTransport

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`
