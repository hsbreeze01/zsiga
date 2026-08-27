# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）创建 `tests/test_config.py`，以单元测试覆盖其公开函数，优先覆盖高圈复杂度函数 `validate_config`（CC=18）。

### 拆解后的子任务

- [ ] 1. **测试基础设施搭建** — 创建 `tests/test_config.py`，建立 import 结构、公用 fixture（如 mock 配置字典、临时 YAML 文件）。（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **低复杂度辅助函数测试** — 覆盖 `_find_config`（路径查找逻辑）、`_resolve_env_vars`（`${VAR}` 递归解析）、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state`（运行时状态读写）。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 3. **高复杂度核心函数测试** — 覆盖 `validate_config`（CC=18）全部校验分支：LLM 必填字段缺失、Target 校验、Pipeline 参数范围、Warning 生成等。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 4. **集成路径测试** — 覆盖 `load_config` 的 YAML 解析→环境变量替换→类实例构建→validate 调用→返回 `ZsigaConfig` 的完整链路，使用 `tmp_path` fixture 隔离文件系统。（预估复杂度：中, 预估 token：~3000 / 无历史参考）

## 边界

### IN scope
- 创建 `tests/test_config.py`（新建文件）
- 测试以下 7 个函数：`_find_config`、`_resolve_env_vars`、`validate_config`、`load_config`、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state`
- 优先覆盖 `validate_config`（CC=18）的多分支逻辑
- 使用 mock/monkeypatch 隔离文件 I/O 和环境变量

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改任何现有测试文件
- 不测试 13 个配置类的 dataclass 字段默认值（属于结构测试，非行为测试）
- 不涉及 LLM 实际调用、网络请求、subprocess

### 依赖的外部条件
- `pytest` 框架及 `conftest_zsiga.py` 中已有 fixture
- `zsiga/config.py` 文件可读且 import 无误
- `pyyaml` 已安装（`yaml.safe_load` / `yaml.dump`）

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且可被 pytest 发现
2. 文件中包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数（BAC-02）
3. 文件中至少 3 个 `def test_` 函数（BAC-03）
4. `python -m pytest tests/test_config.py` 退出码 0，全部测试通过（BAC-04）
5. `validate_config` 的多分支逻辑获得有意义覆盖（至少覆盖 LLM 字段校验、Target 校验、Warning 生成三个路径）

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 计数 ≥ 3
- `grep -E 'def test__find_config|def test__resolve_env_vars|def test_validate_config' tests/test_config.py` 确认三个目标函数存在
- `python -m pytest tests/test_config.py -v --tb=short` 退出码 0
- `ruff check tests/test_config.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/` 下所有已有测试文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- main（默认分支，由 daemon 管理）

### 已知风险
- **已有测试重叠**：`tests/test_config_validation.py` 和 `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` 可能已覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 的部分场景，新测试需避免无意义重复
- **`load_config` 依赖链长**：167 行函数依赖文件系统 + 环境变量 + 多层类构造，mock 策略需谨慎设计
- **auto-generated proposal**：此 proposal 由自演进引擎生成，静态分析数据可能不完整（如类方法列表只列出 5/13 个类）

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类 auto-generated 测试 proposal 历史上被 pushback/reject，无成功执行记录可参考）
