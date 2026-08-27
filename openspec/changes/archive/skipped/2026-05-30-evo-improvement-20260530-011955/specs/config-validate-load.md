# Spec: config-validate-load

## ADDED Requirements

### Requirement: validate_config domain warning branch

The `validate_config()` function SHALL emit a warning when a target's `domain` field is neither `""`, `"self"`, nor `"external"`.

#### Scenario: validate_config_domain_warning

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"invalid_domain"`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (no errors) AND SHALL contain a warning mentioning the domain value

---

### Requirement: load_config YAML parse error

The `load_config()` function SHALL propagate YAML parse errors from `yaml.safe_load`.

#### Scenario: load_config_malformed_yaml

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a file path whose content is malformed YAML (e.g., unbalanced brackets)
- **When** `load_config(path)` is called
- **Then** it SHALL raise a `yaml.YAMLError` or its subclass

---

### Requirement: load_config file not found

The `load_config()` function SHALL raise an appropriate error when the specified path does not exist.

#### Scenario: load_config_missing_file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a file path that does not exist on the filesystem
- **When** `load_config(path)` is called
- **Then** it SHALL raise `FileNotFoundError`

---

### Requirement: load_config with SSH target

The `load_config()` function SHALL correctly parse SSH configuration from the targets section and construct an `SSHConfig` object.

#### Scenario: load_config_ssh_target

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file containing a target with an `ssh` section specifying `host`, `user`, and `port`
- **When** `load_config(path)` is called
- **Then** the resulting config's target SHALL have a non-None `ssh` attribute with the correct `host`, `user`, and `port` values, AND `transport` SHALL default to `"ssh"`

---

### Requirement: load_config with env var resolution

The `load_config()` function SHALL resolve `${VAR}` references in the loaded YAML before constructing config objects.

#### Scenario: load_config_resolves_env_vars

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** environment variable `TEST_API_KEY` is set to `"env_key_123"` AND a YAML config file where `agent.llm.api_key` is `"${TEST_API_KEY}"`
- **When** `load_config(path)` is called
- **Then** the resulting config's `llm.api_key` SHALL be `"env_key_123"`

