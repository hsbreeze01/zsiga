# config-validation.md

## ADDED Requirements

### Requirement: config-validation-test-coverage

`validate_config()` 函数（CC=18）的行为契约 SHALL 通过自动化测试覆盖所有主要分支路径，包括：合法配置通过验证、LLM 必填字段缺失产生错误、温度/令牌数超范围产生警告、目标配置校验、管线参数校验、以及多错误聚合。

#### Scenario: validate-valid-config

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个包含合法 `LLMConfig`（provider="openai", model="gpt-4", api_key="sk-test", temperature=0.3, max_tokens=4096）和一个有效 `TargetConfig`（path="/tmp", transport="local"）的 `ZsigaConfig`
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.valid` 为 `True`，`errors` 列表为空

#### Scenario: validate-missing-llm-provider

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `LLMConfig` 其 `provider` 为空字符串
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "llm.provider is required" 相关错误，且 `valid` 为 `False`

#### Scenario: validate-missing-llm-model

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `LLMConfig` 其 `model` 为空字符串
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "llm.model is required" 相关错误

#### Scenario: validate-missing-llm-api-key

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `LLMConfig` 其 `api_key` 为空字符串
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "llm.api_key is required" 相关错误

#### Scenario: validate-temperature-out-of-range

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `LLMConfig` 其 `temperature` 为 `3.0`（超出 [0.0, 2.0] 范围）
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.warnings` SHALL 包含 "temperature" 相关警告，且 `valid` 为 `True`（温度超范围是警告而非错误）

#### Scenario: validate-max-tokens-non-positive

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `LLMConfig` 其 `max_tokens` 为 `0`
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.warnings` SHALL 包含 "max_tokens" 相关警告，且 `valid` 为 `True`

#### Scenario: validate-empty-targets

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `ZsigaConfig` 其 `targets` 为空字典 `{}`
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "at least one target" 相关错误，且 `valid` 为 `False`

#### Scenario: validate-target-empty-path

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `TargetConfig` 其 `path` 为空字符串
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "path must be a non-empty string" 相关错误

#### Scenario: validate-target-invalid-transport

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `TargetConfig` 其 `transport` 为 `"ftp"`（非 "local" 或 "ssh"）
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "transport must be 'local' or 'ssh'" 相关错误

#### Scenario: validate-ssh-transport-without-ssh-config

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `TargetConfig` 其 `transport` 为 `"ssh"` 但 `ssh` 为 `None`
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含 "SSH transport requires ssh config" 相关错误

#### Scenario: validate-multiple-errors-aggregated

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `ZsigaConfig` 同时缺少 `llm.provider`、`llm.model`、`llm.api_key` 且 `targets` 为空
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.errors` SHALL 包含至少 4 条错误消息，`valid` 为 `False`

#### Scenario: validate-pipeline-max-changes-out-of-range

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `PipelineConfig` 其 `max_changes_per_cycle` 为 `0`（超出 [1, 10] 范围）
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.warnings` SHALL 包含 "max_changes_per_cycle" 相关警告

#### Scenario: validate-pipeline-fix-attempts-out-of-range

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `PipelineConfig` 其 `fix_attempts` 为 `99`（超出 [1, 20] 范围）
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.warnings` SHALL 包含 "fix_attempts" 相关警告

#### Scenario: validate-target-invalid-domain-warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** 一个 `TargetConfig` 其 `domain` 为 `"unknown"`（非 ""、"self" 或 "external"）
- **When** 调用 `validate_config(config)`
- **Then** 返回的 `ValidationResult.warnings` SHALL 包含 "domain should be 'self' or 'external'" 相关警告
