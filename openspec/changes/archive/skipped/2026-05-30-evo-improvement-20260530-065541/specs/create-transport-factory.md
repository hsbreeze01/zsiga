# Spec: create_transport Factory Function

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no SSH config

`create_transport` SHALL return a `LocalTransport` instance when `target_config` has no `ssh` attribute or `ssh` is `None`.

#### Scenario: create_transport returns LocalTransport for local config

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a config object where `ssh` is `None`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

### Requirement: create_transport returns SSHTransport when SSH config present

`create_transport` SHALL return an `SSHTransport` instance initialized with `host`, `user`, `port`, and `key_path` from the `ssh` attribute of `target_config`.

#### Scenario: create_transport returns SSHTransport for ssh config

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh` attribute having `host="myhost"`, `user="ubuntu"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an `SSHTransport` instance with matching `host`, `user`, `port`, `key_path`

