# create-transport-factory

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no SSH config

`create_transport` SHALL return a `LocalTransport` instance when
`target_config` has no `ssh` attribute or when `ssh` is falsy.

#### Scenario: create_transport with no ssh attribute returns LocalTransport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute (e.g. `SimpleNamespace()`)
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport with ssh=None returns LocalTransport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

### Requirement: create_transport returns SSHTransport when SSH config present

`create_transport` SHALL return an `SSHTransport` instance when
`target_config.ssh` is truthy, forwarding `host`, `user`, `port`, and
`key_path` from the SSH config object.

#### Scenario: create_transport with ssh config returns SSHTransport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh` attribute having `host="myhost"`,
  `user="alice"`, `port=2222`, `key_path="/home/alice/.ssh/id_rsa"`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `SSHTransport` with
  `host="myhost"`, `user="alice"`, `port=2222`,
  `key_path="/home/alice/.ssh/id_rsa"`

