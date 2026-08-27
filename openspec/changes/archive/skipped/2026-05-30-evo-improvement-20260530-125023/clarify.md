# clarify.md — add-tests-runner

> ⚠️ **严重预警：此 proposal 基于虚假前提，建议 REJECT**
>
> 目标模块 `zsiga/harness/runner.py` 已有完整测试文件 `tests/test_harness_runner.py`（277 行，28 个 `def test_` 函数，覆盖全部 10 个类）。此 proposal 是自演进引擎 `_scan_code_structure()` basename 匹配 bug 的产物（`"runner"` ≠ `"harness_runner"`），已循环生成 27+ 次并全部被 skip/reject。执行此 proposal 将创建一个与现有测试完全重叠的冗余文件。

---

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（352 行，10 个类）创建 `tests/test_runner.py` 单元测试文件，覆盖公开 API。

### 拆解后的子任务

- [ ] 1. 为 `zsiga/harness/runner.py` 数据类层编写测试（TestEvent/TestStarted/TestPassed/TestFailed/TestError/HarnessResult/TestReport/QualificationReport） (预估复杂度：低, 预估 token：~2000 / 无有效历史参考)
- [ ] 2. 为 `HarnessRunner` 核心方法编写测试（discover/run/results/run_pytest）含 mock 隔离 (预估复杂度：中, 预估 token：~3000 / 无有效历史参考)
- [ ] 3. 验证全部测试通过（pytest exit 0）并满足 BAC (预估复杂度：低, 预估 token：~500 / 无有效历史参考)

## 边界

### IN scope
- 新建 `tests/test_runner.py` 测试文件
- 覆盖 `zsiga/harness/runner.py` 中公开类和方法的单元测试

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改或删除已存在的 `tests/test_harness_runner.py`

### 依赖的外部条件
- **已存在冲突文件**：`tests/test_harness_runner.py` 已包含 28 个测试函数，全面覆盖 runner.py 的全部 10 个类（TestEvent, TestStarted, TestPassed, TestFailed, TestError, HarnessResult, TestReport, QualificationReport, HarnessRunner, _HarnessCollectorPlugin），包括 discover（正常/空目录/不存在目录）、run（通过/失败/错误/多文件）、results 计数等场景
- `zsiga/harness/runner.py` 模块可正常导入
- pytest + ruff 环境可用

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在
2. 包含 `test_module_import` 和 `test_module_smoke` 函数
3. 包含至少 1 个 `def test_` 函数
4. `python -m pytest tests/test_runner.py` 退出码 0

### 验收方式
- 文件存在性检查
- AST 解析验证函数名
- pytest 执行验证

### ⚠️ 关键风险：重复覆盖
即便 BAC 全部通过，新建的 `tests/test_runner.py` 与现有 `tests/test_harness_runner.py` 功能完全重叠，属于冗余操作。真正的修复应针对 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的 basename 匹配逻辑（`"runner"` ≠ `"harness_runner"` 的 bug）。

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（源码只读）
- `tests/test_harness_runner.py`（已存在的完整测试，不应触碰）

### 项目部署分支
- 主分支（main/master）

### 已知风险
- **虚假前提**：proposal 声称模块缺少测试，但 `tests/test_harness_runner.py` 已存在且覆盖完整
- **27+ 次循环拒绝**：此 proposal 已被生成 27+ 次并全部被 skip/reject，是引擎 basename 匹配 bug 的产物
- **冗余文件**：创建 `tests/test_runner.py` 将与现有测试功能重叠，增加维护负担
- **引擎 bug 根因**：`zsiga/intake/evolution.py:1068-1110` 的 `_scan_code_structure()` 将 `test_harness_runner.py` 提取为 `harness_runner`，将 `runner.py` 提取为 `runner`，二者不匹配，导致引擎反复误判"无测试"

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无有效历史参考（此前 27+ 次均未执行，仅 gate 阶段被拦截）
