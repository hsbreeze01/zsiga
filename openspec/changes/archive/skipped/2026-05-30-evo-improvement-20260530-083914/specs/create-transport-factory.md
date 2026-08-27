# Spec: create_transport Factory Function

## ADDED Requirements

### Requirement: create_transport Returns LocalTransport When No SSH Config

`create_transport(target_config)` SHALL return a `LocalTransport` instance when `target_config.ssh` is `None` or falsy.

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh attribute is absent

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

---

### Requirement: create_transport Returns SSHTransport When SSH Config Present

`create_transport(target_config)` SHALL return an `SSHTransport` instance when `target_config.ssh` is truthy, passing `ssh.host`, `ssh.user`, `ssh.port`, and `ssh.key_path` to the constructor.

#### Scenario: create_transport returns SSHTransport when ssh is configured

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport

- **Given** a config object with `ssh` having `host="host1"`, `user="ubuntu"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result is an `SSHTransport` instance with `host="host1"`, `user="ubuntu"`, `port=2222`, `key_path="/key"`

