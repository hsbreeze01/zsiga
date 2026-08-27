# create_transport Factory Function

## ADDED Requirements

### Requirement: create_transport selects LocalTransport when no SSH config

`create_transport(target_config)` SHALL return a `LocalTransport` instance when `target_config` has no `ssh` attribute or the `ssh` attribute is falsy (`None`, empty, etc.).

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the returned object is an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh attribute is missing

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with no `ssh` attribute at all
- **When** `create_transport(target_config)` is called
- **Then** the returned object is an instance of `LocalTransport`

### Requirement: create_transport creates SSHTransport when SSH config present

`create_transport(target_config)` SHALL return an `SSHTransport` instance when `target_config.ssh` is truthy, passing `ssh.host`, `ssh.user`, `ssh.port`, and `ssh.key_path` as constructor arguments.

#### Scenario: create_transport returns SSHTransport with correct parameters

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with `ssh` attribute containing `host="myserver.com"`, `user="deploy"`, `port=2222`, `key_path="/home/deploy/.ssh/key"`
- **When** `create_transport(target_config)` is called
- **Then** the returned object is an instance of `SSHTransport`
- **And** its `host` equals `"myserver.com"`, `user` equals `"deploy"`, `port` equals `2222`, `key_path` equals `"/home/deploy/.ssh/key"`
