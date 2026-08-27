# spec: create-transport-factory

## ADDED Requirements

### Requirement: create_transport returns SSHTransport when ssh config present

`create_transport(target_config)` SHALL inspect `target_config.ssh`. When `ssh` is truthy and has `host`, `user`, `port`, `key_path` attributes, the function MUST return an `SSHTransport` constructed with those values.

#### Scenario: create_transport returns SSHTransport for ssh target

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a mock `target_config` with `ssh` attribute that has `host="h"`, `user="u"`, `port=22`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `SSHTransport` with `host="h"`, `user="u"`, `port=22`, `key_path="/key"`

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a mock `target_config` with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is falsy

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a mock `target_config` with `ssh` attribute set to `False`
- **When** `create_transport(target_config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

