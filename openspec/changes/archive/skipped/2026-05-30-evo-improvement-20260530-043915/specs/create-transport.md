# create_transport Factory Test Coverage

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no SSH config

`create_transport(target_config)` SHALL return a `LocalTransport` instance when `target_config.ssh` is `None` or falsy.

#### Scenario: create_transport with ssh=None returns LocalTransport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be a `LocalTransport` instance

#### Scenario: create_transport with missing ssh attribute returns LocalTransport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with no `ssh` attribute (e.g. `SimpleNamespace()`)
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be a `LocalTransport` instance

### Requirement: create_transport returns SSHTransport when SSH config present

`create_transport(target_config)` SHALL return an `SSHTransport` instance when `target_config.ssh` is truthy, forwarding `ssh.host`, `ssh.user`, `ssh.port`, `ssh.key_path`.

#### Scenario: create_transport with ssh config returns SSHTransport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` with `ssh=SimpleNamespace(host="myhost", user="ubuntu", port=2222, key_path="/key")`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an `SSHTransport` instance with `host="myhost"`, `user="ubuntu"`, `port=2222`, `key_path="/key"`

