# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行，7 函数，13 类）创建独立的单元测试文件 `tests/test_config.py`，覆盖其公开函数（`_find_config`、`_resolve_env_vars`、`validate_config`），确保 `pytest` 通过。不修改源码。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_config.py` 骨架并编写 `_find_config` 测试组 (预估复杂度：低, 预估 token：~1500)
  - 测试当前目录存在 `zsiga.yaml` 时返回该路径
  - 测试当前目录不存在时回退到 `~/.zsiga/zsiga.yaml`
  - 测试两处均不存在时抛出 `FileNotFoundError`
  - 使用 `tmp_path` 或 `monkeypatch` 隔离文件系统

- [ ] 2. 编写 `_resolve_env_vars` 测试组 (预估复杂度：低, 预估 token：~1500)
  - 测试 `${VAR}` 替换为环境变量值
  - 测试环境变量不存在时保留原始占位符
  - 测试嵌套 dict / list 中的递归替换
  - 测试非字符串值原样返回

- [ ] 3. 编写 `validate_config` 测试组（CC=18 高复杂度函数） (预估复杂度：中, 预估 token：~3000)
  - 构造合法 `ZsigaConfig` → 断言 `valid=True`
  - 缺少 LLM 必填字段（provider/model/api_key）→ 断言 `errors` 非空
  - target transport=ssh 但缺少 SSH 配置 → 断言 `errors` 非空
  - pipeline 超出范围值 → 断言 `warnings` 非空
  - 至少覆盖 4 条分支路径以验证高 CC 函数的关键决策点

## 边界

### IN scope
- 新建 `tests/test_config.py`
- 覆盖 3 个目标函数：`_find_config`、`_resolve_env_vars`、`validate_config`
- 包含至少 3 个 `def test_` 函数
- `pytest tests/test_config.py` 退出码 0

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不覆盖 `load_config`（167 行超大函数，已有 `test_config_validation.py` 集成测试）
- 不覆盖 `_runtime_state_path`、`load_runtime_state`、`save_runtime_state`
- 不覆盖 13 个数据类（`SSHConfig`、`TargetConfig` 等），已有 `test_config_validation.py` 覆盖
- 不修改或合并已有的 `tests/test_config_validation.py`、`tests/test_config_diff.py`

### 依赖的外部条件
- `zsiga/config.py` 源码保持稳定（函数签名和行号不发生破坏性变更）
- `pytest` 框架可用
- 已有测试文件 `tests/test_config_validation.py`（426 行，~30 测试）已覆盖 `validate_config` 和 `load_config` 的部分场景——新建测试可能与已有测试存在重叠，但 BAC 明确要求在 `test_config.py` 中创建指定函数

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在
2. 文件中包含函数 `test__find_config`、`test__resolve_env_vars`、`test_validate_config`
3. 文件中包含至少 3 个 `def test_` 函数
4. `python -m pytest tests/test_config.py` 退出码 0

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 计数 ≥ 3
- `grep 'def test__find_config\|def test__resolve_env_vars\|def test_validate_config' tests/test_config.py` 确认三个函数名存在
- `python -m pytest tests/test_config.py -x --tb=short` 退出码 0
- `ruff check tests/test_config.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（只读分析）
- `tests/test_config_validation.py`（已有覆盖，不碰）
- `tests/test_config_diff.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（已有 `_find_config` / `_resolve_env_vars` 覆盖）

### 项目部署分支
- `zsiga-self-evolve`（zsiga 自演进目标，domain: self）

### 已知风险
- **与已有测试重叠**：`tests/test_config_validation.py` 已有 ~30 个测试覆盖 `validate_config` 和 `load_config`；`test_spec_evo_improvement_..._config_unit_coverage.py` 已覆盖 `_find_config` 和 `_resolve_env_vars`。新建 `test_config.py` 可能产生重复测试，增加维护负担
- **22+ 轮循环未打破**：同名 proposal `add-tests-config` 已迭代 22+ 次全部 skipped/archived，从未进入实现阶段。失败原因多为 deploy branch drift、phase contract 缺失等 pipeline 阻塞，非技术可行性问题
- **BAC 仅要求最低覆盖**：BAC 只要求 3 个 `def test_` 函数且函数名匹配，不要求高覆盖率。实际覆盖可能停留在表面 smoke test 级别

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（同名 proposal 从未进入实现阶段）
