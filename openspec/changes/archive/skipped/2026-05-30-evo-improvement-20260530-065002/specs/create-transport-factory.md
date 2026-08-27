# create-transport-factory.md — Delta Spec

## ADDED Requirements

### Requirement: create_transport returns LocalTransport when no SSH config

`create_transport(target_config)` SHALL return a `LocalTransport` instance when
`target_config` has no `ssh` attribute or the `ssh` attribute is falsy (`None`,
empty, etc.).

#### Scenario: create_transport returns LocalTransport without ssh config

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object with no `ssh` attribute (or `ssh=None`)
- **When** `create_transport(target_config)` is called
- **Then** the returned transport is an instance of `LocalTransport`

---

### Requirement: create_transport returns SSHTransport when SSH config present

`create_transport(target_config)` SHALL return an `SSHTransport` instance
configured with `host`, `user`, `port`, `key_path` from `target_config.ssh`
when the `ssh` attribute is truthy.

#### Scenario: create_transport returns SSHTransport with ssh config

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` object whose `ssh` attribute has `host="srv"`,
  `user="u"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** the returned transport is an `SSHTransport` instance with
  `host="srv"`, `user="u"`, `port=2222`, `key_path="/key"`

