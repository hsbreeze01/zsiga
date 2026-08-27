# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
Proposal 声称为 `zsiga/harness/runner.py`（352 行, 10 类）添加单元测试文件 `tests/test_runner.py`，声称该模块"缺少测试文件"，是潜在风险点。

### 事实核查（关键发现）
**此 proposal 的核心前提不成立：** `tests/test_harness_runner.py`（277 行，20+ 个 `def test_` 函数）已全面覆盖 `zsiga/harness/runner.py` 的全部 10 个公开类（`TestEvent`, `TestStarted`, `TestPassed`, `TestFailed`, `TestError`, `HarnessResult`, `TestReport`, `QualificationReport`, `HarnessRunner`, `_HarnessCollectorPlugin`）。

**根因：** 自演进引擎 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 使用 `os.path.basename()` 做匹配——将 `runner.py` 提取为 `"runner"`，但 `test_harness_runner.py` 去掉前缀后是 `"harness_runner"`，二者永远不匹配。此 proposal 已被生成 27+ 次，全部被 skip/reject。

### 拆解后的子任务

- [ ] 1. 修复 `_scan_code_structure()` 的 basename 匹配逻辑（预估复杂度：中, 预估 token：~4000）
  - 文件：`zsiga/intake/evolution.py`（L1068-L1113 区域）
  - 将 basename 匹配改为子串包含匹配或 glob 匹配，使 `test_harness_runner.py` 能被正确关联到 `runner.py`

## 边界

### IN scope
- 修复 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的测试文件发现逻辑
- 确保修复后引擎不再为已有测试覆盖的模块生成重复 proposal

### OUT of scope
- ~~创建 `tests/test_runner.py`~~ — 测试已存在于 `tests/test_harness_runner.py`
- 修改 `zsiga/harness/runner.py` 源码
- 修改 `tests/test_harness_runner.py` 已有测试

### 依赖的外部条件
- 需确认修复后 `_scan_code_structure()` 对其他模块的匹配不受影响（回归风险）

## 目标

### 成功标准
1. `_scan_code_structure()` 能正确发现 `tests/test_harness_runner.py` 覆盖了 `zsiga/harness/runner.py`
2. 引擎不再为 `runner.py` 生成 `add-tests-runner` proposal
3. 对其他已有 `test_{prefix}_{module}.py` 命名模式的模块（如 `test_phase_duration.py` 覆盖 `duration_predictor.py`），匹配也正确
4. 现有测试 `pytest tests/test_evolution_proposal_quality.py` 通过

### 验收方式
- 运行 `pytest tests/test_evolution_proposal_quality.py` 确认无回归
- 手动调用 `_scan_code_structure()` 验证 `modules_without_tests` 不再包含 `zsiga/harness/runner.py`
- ruff check 通过

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`
- `tests/test_harness_runner.py`

### 项目部署分支
- deploy

### 已知风险
- **回归风险：** 修改 basename 匹配逻辑可能影响其他模块的测试发现结果，需全面验证
- **循环空转历史：** 此 proposal 模式已触发 27+ 次空转，修复后需观察至少 2 个引擎周期确认不再复发
- **其他同类误判：** `duration_predictor.py` 也存在类似问题（测试在 `test_phase_duration.py` 而非 `test_duration_predictor.py`），修复方案应一并解决

### 预估 token 消耗
- prompt: ~5000
- completion: ~3000
- 数据来源: 无历史参考（属于引擎修复而非测试创建）
