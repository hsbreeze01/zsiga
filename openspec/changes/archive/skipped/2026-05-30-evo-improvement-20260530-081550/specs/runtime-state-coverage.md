# runtime-state-coverage

## Context

`zsiga/config.py` 的核心函数（`validate_config`, `load_config`, `_find_config`, `_resolve_env_vars`）
及全部 13 个数据类已有 **52+ 个测试** 覆盖于 `tests/test_config_validation.py` 和
`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`。

自演进引擎因 `basename` 匹配 bug（只查 `test_config.py`，不识别 `test_config_validation.py`）
持续生成虚假 proposal。本 change 仅关注最后确认的小范围边缘场景。

## ADDED Requirements

### Requirement: runtime-state-path-resolution

`_runtime_state_path()` SHALL 返回 `Path` 对象，路径由以下规则决定：
- 若 `ZSIGA_HOME` 环境变量非空 → `Path(ZSIGA_HOME) / "data/runtime_state.yaml"`
- 否则 → 配置文件所在目录 / `"data/runtime_state.yaml"`

#### Scenario: path_with_zsiga_home_env

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path

- **Given** 环境变量 `ZSIGA_HOME` 设置为 `/tmp/zh`
- **When** 调用 `_runtime_state_path()`
- **Then** 返回 `Path("/tmp/zh/data/runtime_state.yaml")`

#### Scenario: path_without_zsiga_home_falls_back_to_config_dir

- **testable**: false
- **Given** 环境变量 `ZSIGA_HOME` 未设置
- **When** 调用 `_runtime_state_path()`
- **Then** 返回 `_find_config().parent / "data/runtime_state.yaml"`
> 依赖 `_find_config()` 的文件系统探测，需 mock 或 fixture 准备完整目录结构；
> 已在 `test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` 间接覆盖。

### Requirement: load-runtime-state-robustness

`load_runtime_state()` SHALL 从 `_runtime_state_path()` 指定的 YAML 文件读取并返回 `dict`。
当文件不存在或内容不可解析时 SHALL 返回空 `dict`（不抛异常）。

#### Scenario: load_returns_empty_on_missing_file

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state

- **Given** `_runtime_state_path()` 指向一个不存在的文件
- **When** 调用 `load_runtime_state()`
- **Then** 返回 `{}`

#### Scenario: load_returns_empty_on_corrupt_yaml

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state

- **Given** `_runtime_state_path()` 指向一个包含无效 YAML 的文件
- **When** 调用 `load_runtime_state()`
- **Then** 返回 `{}`（不抛异常）

#### Scenario: load_returns_parsed_dict_on_valid_file

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state

- **Given** `_runtime_state_path()` 指向包含 `{"active_target": "zsiga", "count": 5}` 的 YAML 文件
- **When** 调用 `load_runtime_state()`
- **Then** 返回 `{"active_target": "zsiga", "count": 5}`

### Requirement: save-runtime-state-persistence

`save_runtime_state(state)` SHALL 将 `state` dict 序列化为 YAML 并写入
`_runtime_state_path()` 指定的路径。若父目录不存在 SHALL 自动创建。

#### Scenario: save_creates_parent_dirs_and_writes_yaml

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state

- **Given** `_runtime_state_path()` 指向一个父目录不存在的路径
- **When** 调用 `save_runtime_state({"active_target": "test"})`
- **Then** 父目录被创建，且后续 `load_runtime_state()` 返回 `{"active_target": "test"}`

#### Scenario: save_roundtrip_preserves_unicode

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state

- **Given** 一个包含 Unicode 键值对的 dict
- **When** 调用 `save_runtime_state({"标签": "测试", "status": "运行中"})` 后再 `load_runtime_state()`
- **Then** 返回的 dict 与原始 dict 相同
