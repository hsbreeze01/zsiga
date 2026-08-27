# config-util-functions.md

## ADDED Requirements

### Requirement: config-util-test-coverage

`zsiga/config.py` 中 `_find_config()` 和 `_resolve_env_vars()` 的行为契约 SHALL 通过自动化测试覆盖，确保环境变量解析和配置文件查找的每个分支均被独立验证。

#### Scenario: find-config-in-current-directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** 当前工作目录下存在文件 `zsiga.yaml` 且 `Path.home()` 下不存在 `~/.zsiga/zsiga.yaml`
- **When** 调用 `_find_config()`
- **Then** 返回 `Path("zsiga.yaml")`（当前目录下的相对路径）

#### Scenario: find-config-home-fallback

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** 当前工作目录下不存在 `zsiga.yaml`，且 `Path.home() / ".zsiga" / "zsiga.yaml"` 存在
- **When** 调用 `_find_config()`
- **Then** 返回 `Path.home() / ".zsiga" / "zsiga.yaml"` 的绝对路径

#### Scenario: find-config-not-found

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** 当前工作目录和 `Path.home() / ".zsiga/"` 下均不存在 `zsiga.yaml`
- **When** 调用 `_find_config()`
- **Then** SHALL 抛出 `FileNotFoundError` 异常，消息包含 "zsiga.yaml not found"

#### Scenario: resolve-env-vars-matching

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** 环境变量 `MY_KEY` 已设置为 `"secret123"`
- **When** 调用 `_resolve_env_vars("${MY_KEY}")`
- **Then** 返回 `"secret123"`

#### Scenario: resolve-env-vars-no-match

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** 环境变量 `UNDEFINED_VAR_XYZ` 未设置
- **When** 调用 `_resolve_env_vars("${UNDEFINED_VAR_XYZ}")`
- **Then** 返回空字符串 `""`

#### Scenario: resolve-env-vars-dict

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** 环境变量 `DICT_KEY` 已设置为 `"resolved_value"`
- **When** 调用 `_resolve_env_vars({"k": "${DICT_KEY}", "plain": "text"})`
- **Then** 返回 `{"k": "resolved_value", "plain": "text"}`

#### Scenario: resolve-env-vars-list

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** 环境变量 `LIST_ITEM` 已设置为 `"item_val"`
- **When** 调用 `_resolve_env_vars(["${LIST_ITEM}", 42])`
- **Then** 返回 `["item_val", 42]`

#### Scenario: resolve-env-vars-non-string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** 输入为非字符串原始值（整数 `42` 或 `None`）
- **When** 调用 `_resolve_env_vars(42)` 或 `_resolve_env_vars(None)`
- **Then** 原样返回输入值（`42` 或 `None`）

#### Scenario: resolve-env-vars-non-placeholder-string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** 输入为普通字符串（不以 `${` 开头且不以 `}` 结尾）
- **When** 调用 `_resolve_env_vars("hello")`
- **Then** 原样返回 `"hello"`
