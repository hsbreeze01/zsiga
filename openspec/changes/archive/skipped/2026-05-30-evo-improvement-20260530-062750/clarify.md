# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）创建 `tests/test_config.py`，覆盖其公开函数，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 关键事实校准
**⚠️ 此 proposal 已在 archive 中循环 22+ 次，全部 skipped/archived。根因是自演进引擎只匹配 `tests/test_config.py` 文件名，忽略了项目中已有的测试覆盖。**

已有测试文件：
- `tests/test_config_validation.py`（426 行, 40+ 测试）— 覆盖 `validate_config`、`load_config` 集成、`ValidationResult`、`ConfigValidationError`、`LLMFastConfig` 等
- `tests/test_config_diff.py`（98 行）— 覆盖 config diff 功能
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` — 覆盖 `_find_config`、`_resolve_env_vars`、`_runtime_state_path`

项目 glossary 中已存在的测试类（分布在上述文件中）：
- 数据类构造：TestSSHConfigConstruction, TestTargetConfigDefaults, TestLLMConfigDefaults, TestLLMFastConfigConstruction, TestCompactionConfigDefaults, TestPipelineConfigDefaults, TestIntakeConfigDefaults, TestSafetyConfigDefaults, TestGithubConfigDefaults, TestLoggingConfig, TestZsigaConfigConstruction
- 环境变量解析：TestResolveExistingEnvVar, TestResolveMissingEnvVar, TestResolveDictRecursively, TestResolveListRecursively, TestPlainStringPassthrough, TestNonStringPassthrough, TestNestedStructureResolution
- 配置查找：TestFindConfigInCurrentDir, TestFindConfigInHomeDir, TestFindConfigRaisesFileNotFound
- 配置加载集成：TestLoadConfigWithSSHTarget, TestLoadConfigWithPipelineOverrides, TestLoadConfigWithCompactionOverrides, TestLoadConfigWithEnvVarSubstitution, TestLoadConfigWithGithubSection, TestLoadConfigWithLoggingSection, TestLoadConfigWithSafetyOverrides, TestLoadConfigWithIntakeApiPoll
- 运行时状态：TestRuntimeStatePathWithZsigaHome

**结论：`validate_config`、`load_config`、`_find_config`、`_resolve_env_vars`、`_runtime_state_path` 以及所有 13 个数据类的构造均已有充分测试覆盖。实际缺失覆盖的仅有 `load_runtime_state()` 和 `save_runtime_state()` 的直接单元测试。**

### 拆解后的子任务
- [ ] 1. 补充 `load_runtime_state()` / `save_runtime_state()` 单元测试（预估复杂度：低, 预估 token：~2000 / 无历史参考）
  - 测试正常读写流程（mock 文件 I/O）
  - 测试文件不存在时的 fallback 行为
  - 测试 YAML 解析异常时的错误处理
  - 追加到已有 `tests/test_config_validation.py` 或新建 `tests/test_config.py`（仅含这 2 个函数的测试）

## 边界

### IN scope
- 为 `load_runtime_state()` 和 `save_runtime_state()` 添加直接单元测试
- 满足 BAC-01 ~ BAC-04 验收标准

### OUT of scope
- 重复覆盖 `validate_config`（已在 `test_config_validation.py` 中全面覆盖）
- 重复覆盖 `load_config`（已在 `test_config_validation.py` 中集成测试）
- 重复覆盖 `_find_config` / `_resolve_env_vars`（已在 spec_evo 测试文件中覆盖）
- 重复覆盖 13 个数据类的构造（已在 `test_config_validation.py` 中覆盖）
- 修改 `zsiga/config.py` 源码

### 依赖的外部条件
- `zsiga/config.py` 中 `load_runtime_state()` 和 `save_runtime_state()` 的签名和行为保持稳定
- pytest 框架可用
- `pyyaml` 可用于构造测试 fixture

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在
2. 文件中包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数名（满足 BAC-02，可为 thin wrapper 委托已有覆盖）
3. 文件中包含至少 3 个 `def test_` 函数（BAC-03）
4. `python -m pytest tests/test_config.py` 退出码 0（BAC-04）
5. **新增实质覆盖**：`load_runtime_state()` 和 `save_runtime_state()` 有独立的单元测试，不与已有测试重复

### 验收方式
- `test -f tests/test_config.py` 文件存在
- `grep -c 'def test_' tests/test_config.py` ≥ 3
- `python -m pytest tests/test_config.py -v` 全部通过
- 确认无重复测试（与 `test_config_validation.py` 的测试类名不重复）

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/test_config_validation.py`（已有 426 行成熟测试，不扰动）
- `tests/test_config_diff.py`（已有 98 行成熟测试，不扰动）

### 项目部署分支
- deploy（根据项目配置）

### 已知风险
- **循环 proposal 风险**：同名 `add-tests-config` 已循环 22+ 次，引擎反复生成是因文件名匹配 bug，非测试缺失。本次应只做最小补充，避免再次空转。
- **重复测试风险**：BAC-02 要求的 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 已在现有文件中充分覆盖，新建文件中这些测试应为 minimal placeholder 或 import 委托，不应复制测试逻辑。
- **deploy branch drift**：近期 10+ 次 pipeline 中断由 deploy branch drift 导致（见 pattern warning），需注意。

### 预估 token 消耗
- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考（同类 proposal 从未进入实现阶段）
