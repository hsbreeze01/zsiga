# create_transport Factory Function

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no SSH config

When `target_config` has no `ssh` attribute (or it is falsy), `create_transport`
SHALL return a `LocalTransport` instance.

#### Scenario: returns LocalTransport for config without ssh

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: returns LocalTransport when ssh attribute is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with `ssh = None`
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

### Requirement: create_transport returns SSHTransport when SSH config present

When `target_config.ssh` is truthy, `create_transport` SHALL return an
`SSHTransport` instance initialized with `ssh.host`, `ssh.user`, `ssh.port`,
`ssh.key_path`.

#### Scenario: returns SSHTransport for config with ssh

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport

- **Given** a config object where `ssh` is a namespace with `host="srv"`,
  `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result is an `SSHTransport` instance with `host="srv"`,
  `user="alice"`, `port=2222`, `key_path="/key"`

