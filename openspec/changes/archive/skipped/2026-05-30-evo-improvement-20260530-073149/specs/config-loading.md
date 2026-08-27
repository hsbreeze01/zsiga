# spec: config-loading

## ADDED Requirements

### Requirement: load_config SSH target parsing

`load_config` SHALL parse the `ssh` subsection of a target and construct an
`SSHConfig` with the provided fields.

#### Scenario: Load config with SSH target

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with a target that has `transport: ssh` and an `ssh` section
  containing `host: myserver`, `user: deploy`, `port: 2222`
- **When** `load_config(path=<that_file>)` is called
- **Then** the returned `ZsigaConfig` SHALL have a target whose `ssh` attribute is an
  `SSHConfig` with `host="myserver"`, `user="deploy"`, `port=2222`

### Requirement: load_config compaction overrides

`load_config` SHALL apply compaction settings from the `pipeline.compaction` section,
overriding defaults.

#### Scenario: Load config with custom compaction

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline.compaction.threshold_chars: 50000`
- **When** `load_config(path=<that_file>)` is called
- **Then** the returned config's `pipeline.compaction.threshold_chars` SHALL be `50000`

### Requirement: load_config github section

`load_config` SHALL parse the `github` section into a `GithubConfig`.

#### Scenario: Load config with github section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `github.token: "ghp_abc"` and `github.owner: "myorg"`
- **When** `load_config(path=<that_file>)` is called
- **Then** the returned config's `github.token` SHALL be `"ghp_abc"` AND
  `github.owner` SHALL be `"myorg"`

### Requirement: load_config logging section

`load_config` SHALL parse the `logging` section into a `LoggingConfig`.

#### Scenario: Load config with logging section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `logging.level: "debug"` and `logging.format: "json"`
- **When** `load_config(path=<that_file>)` is called
- **Then** the returned config's `logging_config.level` SHALL be `"DEBUG"` AND
  `logging_config.fmt` SHALL be `"json"`

### Requirement: load_config safety section

`load_config` SHALL parse the `safety` section into a `SafetyConfig`.

#### Scenario: Load config with safety overrides

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `safety.require_approval: false` and `safety.max_files_per_task: 5`
- **When** `load_config(path=<that_file>)` is called
- **Then** the returned config's `safety.require_approval` SHALL be `False` AND
  `safety.max_files_per_task` SHALL be `5`

### Requirement: load_config intake api_poll section

`load_config` SHALL parse the `intake.api_poll` section into `IntakeConfig` fields.

#### Scenario: Load config with api_poll

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `intake.api_poll.url: "https://api.example.com"` and
  `intake.api_poll.poll_interval_seconds: 120`
- **When** `load_config(path=<that_file>)` is called
- **Then** the returned config's `intake.api_url` SHALL be `"https://api.example.com"` AND
  `intake.poll_interval_seconds` SHALL be `120`
