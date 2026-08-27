# config-load.md

## ADDED Requirements

### Requirement: config-load-test-coverage

`load_config()` 函数的集成行为 SHALL 通过自动化测试覆盖，使用 mock/临时文件隔离外部依赖，验证 YAML 解析、环境变量注入、配置校验链路和错误处理路径。

#### Scenario: load-config-valid-yaml

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** 一个有效的 YAML 配置文件，包含 `agent.llm`（provider、model、api_key）和 `targets.t1`（path）
- **When** 调用 `load_config(str(config_path))`
- **Then** 返回的 `ZsigaConfig` 的 `llm.provider` 等于 YAML 中的 provider 值，`targets` 包含键 `"t1"`

#### Scenario: load-config-file-not-found

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** 指定的配置文件路径不存在
- **When** 调用 `load_config("/nonexistent/path/zsiga.yaml")`
- **Then** SHALL 抛出异常（`FileNotFoundError` 或 `OSError`）

#### Scenario: load-config-validation-error

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** 一个 YAML 配置文件，其 `agent.llm.api_key` 为空字符串
- **When** 调用 `load_config(str(config_path))`
- **Then** SHALL 抛出 `ConfigValidationError` 异常，且 `exception.result.valid` 为 `False`

#### Scenario: load-config-resolves-env-vars

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** 一个 YAML 配置文件，其 `api_key` 值为 `"${TEST_API_KEY}"`，且环境变量 `TEST_API_KEY` 已设置为 `"sk-from-env"`
- **When** 调用 `load_config(str(config_path))`
- **Then** 返回的 `ZsigaConfig.llm.api_key` 等于 `"sk-from-env"`

#### Scenario: load-config-default-values

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** 一个最小化的 YAML 配置文件，仅包含必填字段（`agent.llm` 的 provider/model/api_key 和一个 target 的 path），不包含 `pipeline`、`intake`、`safety` 等可选段
- **When** 调用 `load_config(str(config_path))`
- **Then** 返回的 `ZsigaConfig.pipeline.max_changes_per_cycle` 等于默认值 `3`，`intake.mode` 等于默认值 `"dir_scan"`

#### Scenario: load-config-ssh-target

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** 一个 YAML 配置文件，其 target 包含 `ssh` 子段（host、user、port）且 `transport` 为 `"ssh"`
- **When** 调用 `load_config(str(config_path))`
- **Then** 返回的 `TargetConfig.ssh.host` 等于 YAML 中的 host 值，且 `TargetConfig.transport` 等于 `"ssh"`
