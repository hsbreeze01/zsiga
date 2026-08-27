# create_transport Factory Function

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no ssh config

When `target_config` has no `ssh` attribute or `ssh` is `None`/falsy,
`create_transport` SHALL return a `LocalTransport` instance.

#### Scenario: create_transport returns LocalTransport for None ssh

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a target_config object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh attr missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a target_config object with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

### Requirement: create_transport returns SSHTransport when ssh config present

When `target_config.ssh` is truthy, `create_transport` SHALL return an
`SSHTransport` instance constructed with `host=ssh.host`, `user=ssh.user`,
`port=ssh.port`, `key_path=ssh.key_path`.

#### Scenario: create_transport returns SSHTransport with ssh config

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a target_config object with an `ssh` attribute having `host="myhost", user="alice", port=2222, key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result is an `SSHTransport` instance with `host=="myhost"`, `user=="alice"`, `port==2222`, `key_path=="/key"`

