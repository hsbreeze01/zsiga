# config-validation

## ADDED Requirements

### Requirement: validate-config-valid-config

`validate_config` SHALL return a `ValidationResult` with `valid=True` and no errors when given a fully valid `ZsigaConfig`.

#### Scenario: all-fields-valid

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a valid `LLMConfig` (provider="openai", model="gpt-4", api_key="sk-xxx", temperature=0.3, max_tokens=4096)
- **And** at least one `TargetConfig` with transport="local" and a non-empty path
- **And** a default `PipelineConfig`
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult.errors` SHALL be empty
- **And** `ValidationResult.valid` SHALL be `True`

---

### Requirement: validate-config-missing-llm-fields

`validate_config` SHALL report errors when required LLM fields (provider, model, api_key) are empty strings.

#### Scenario: empty-provider-model-apikey

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with an `LLMConfig` having provider="", model="", api_key=""
- **And** at least one valid `TargetConfig`
- **When** `validate_config(config)` is called
- **Then** `ValidationResult.errors` SHALL contain at least one error mentioning "provider"
- **And** `ValidationResult.errors` SHALL contain at least one error mentioning "model"
- **And** `ValidationResult.errors` SHALL contain at least one error mentioning "api_key"
- **And** `ValidationResult.valid` SHALL be `False`

---

### Requirement: validate-config-ssh-target-without-ssh-config

`validate_config` SHALL report an error when a target has `transport="ssh"` but no SSH configuration or an empty SSH host.

#### Scenario: ssh-transport-no-ssh-config

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a valid `LLMConfig`
- **And** a `TargetConfig` with transport="ssh" and `ssh=None`
- **When** `validate_config(config)` is called
- **Then** `ValidationResult.errors` SHALL contain at least one error mentioning "SSH"
- **And** `ValidationResult.valid` SHALL be `False`

---

### Requirement: validate-config-pipeline-out-of-range-warnings

`validate_config` SHALL produce warnings (not errors) when pipeline parameters fall outside recommended ranges.

#### Scenario: max-changes-per-cycle-out-of-range

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with valid LLM and target config
- **And** a `PipelineConfig` with `max_changes_per_cycle=99`
- **When** `validate_config(config)` is called
- **Then** `ValidationResult.warnings` SHALL contain at least one warning mentioning "max_changes_per_cycle"
- **And** `ValidationResult.valid` SHALL be `True` (warnings do not block validity)

---

### Requirement: validate-config-no-targets-error

`validate_config` SHALL report an error when the targets dictionary is empty.

#### Scenario: empty-targets

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a valid `LLMConfig`
- **And** an empty `targets` dictionary `{}`
- **When** `validate_config(config)` is called
- **Then** `ValidationResult.errors` SHALL contain at least one error mentioning "target"
- **And** `ValidationResult.valid` SHALL be `False`

---

### Requirement: validate-config-invalid-transport-error

`validate_config` SHALL report an error when a target has an unsupported transport value.

#### Scenario: invalid-transport-value

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a valid `LLMConfig`
- **And** a `TargetConfig` with transport="ftp"
- **When** `validate_config(config)` is called
- **Then** `ValidationResult.errors` SHALL contain at least one error mentioning "transport"
- **And** `ValidationResult.valid` SHALL be `False`
