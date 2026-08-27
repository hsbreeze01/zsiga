# config-loading

## ADDED Requirements

### Requirement: Config file discovery

The `_find_config` function SHALL search for `zsiga.yaml` in the current working directory first,
then in `~/.zsiga/zsiga.yaml`. It MUST raise `FileNotFoundError` when no config file is found.

#### Scenario: Find config in current directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing `zsiga.yaml`
- **When** `_find_config` is called with the cwd set to that directory
- **Then** the returned path points to the `zsiga.yaml` in that directory

#### Scenario: Find config in home directory fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory but one exists at `~/.zsiga/zsiga.yaml`
- **When** `_find_config` is called
- **Then** the returned path points to the home directory config

#### Scenario: Raise FileNotFoundError when no config

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in either the current directory or `~/.zsiga/`
- **When** `_find_config` is called
- **Then** `FileNotFoundError` is raised with message containing "zsiga.yaml not found"

### Requirement: Config loading with SSH target

The `load_config` function SHALL correctly parse SSH configuration from target entries,
constructing an `SSHConfig` object when the `ssh` key is present in a target definition.

#### Scenario: Load config with SSH target

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with a target containing `ssh: {host: "myhost", user: "deploy", port: 2222}`
- **When** `load_config` is called with that file path
- **Then** the resulting target has an `SSHConfig` with host="myhost", user="deploy", port=2222

### Requirement: Config loading with pipeline overrides

The `load_config` function SHALL correctly override default pipeline values from the YAML
`pipeline` section, including nested `compaction` and `explore_pool` subsections.

#### Scenario: Load config with pipeline overrides

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {max_changes_per_cycle: 5, enrich_max_turns: 30}`
- **When** `load_config` is called with that file path
- **Then** the resulting pipeline has max_changes_per_cycle == 5 and enrich_max_turns == 30

#### Scenario: Load config with compaction overrides

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {compaction: {enabled: false, threshold_chars: 50000}}`
- **When** `load_config` is called with that file path
- **Then** the resulting pipeline.compaction has enabled == False and threshold_chars == 50000

### Requirement: Config loading with env var substitution

The `load_config` function SHALL apply `_resolve_env_vars` to the raw YAML before parsing,
allowing environment variable references in config values.

#### Scenario: Load config with env var in api_key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** environment variable `MY_API_KEY` is set to "sk-from-env" and a YAML config file
  referencing `api_key: "${MY_API_KEY}"`
- **When** `load_config` is called with that file path
- **Then** the resulting llm.api_key == "sk-from-env"

### Requirement: Config loading with github section

The `load_config` function SHALL parse the optional `github` section into a `GithubConfig`.

#### Scenario: Load config with github section

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `github: {token: "ghp_xxx", owner: "myorg", issue_integration: true}`
- **When** `load_config` is called with that file path
- **Then** the resulting github has token == "ghp_xxx", owner == "myorg", issue_integration is True

### Requirement: Config loading with logging section

The `load_config` function SHALL parse the optional `logging` section into a `LoggingConfig`,
uppercasing the level value.

#### Scenario: Load config with logging section

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `logging: {level: "debug", format: "json", file: "/tmp/zsiga.log"}`
- **When** `load_config` is called with that file path
- **Then** the resulting logging_config has level == "DEBUG", fmt == "json", file == "/tmp/zsiga.log"

### Requirement: Config loading with safety section

The `load_config` function SHALL parse the `safety` section into a `SafetyConfig`.

#### Scenario: Load config with safety overrides

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `safety: {require_approval: false, max_files_per_task: 10}`
- **When** `load_config` is called with that file path
- **Then** the resulting safety has require_approval == False and max_files_per_task == 10

### Requirement: Config loading with intake section

The `load_config` function SHALL parse the `intake` section into an `IntakeConfig`,
including nested `dir_scan` and `api_poll` subsections.

#### Scenario: Load config with intake api_poll

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `intake: {mode: "api_poll", api_poll: {url: "https://example.com/api", poll_interval_seconds: 60}}`
- **When** `load_config` is called with that file path
- **Then** the resulting intake has mode == "api_poll", api_url == "https://example.com/api",
  poll_interval_seconds == 60

