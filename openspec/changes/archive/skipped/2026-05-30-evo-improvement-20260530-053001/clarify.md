# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
Proposal 要求为 `zsiga/harness/runner.py`（352 行，10 个类）创建测试文件 `tests/test_runner.py`，声称该模块"缺少测试文件"。

### ⛔ 核心事实校验：需求前提为假

**`tests/test_harness_runner.py` 已存在（277 行，28 个 `def test_` 函数），全面覆盖了 `zsiga/harness/runner.py` 的所有 10 个公开类。**

| 已有测试类 | 覆盖目标 | 测试数量 |
|---|---|---|
| `TestEventDataclasses` | TestEvent/TestStarted/TestPassed/TestFailed/TestError | 4 |
| `TestHarnessResult` | HarnessResult 聚合逻辑 | 2 |
| `TestHarnessRunnerDiscover` | HarnessRunner.discover() 文件发现 | 3 |
| `TestHarnessRunnerRun` | HarnessRunner.run() 执行与事件发射 | 7 |
| `TestHarnessRunnerPytestFailClosed` | HarnessRunner.run_pytest() fail-closed 行为 | 4 |
| `TestMockLLMClient` / `TestMockTransport` / `TestTempGitRepo`（test_harness_conftest.py, 152 行） | harness 模块 conftest 辅助 | 19 |

### 拆解后的子任务

- [ ] 1. **确认无需执行** — 本 proposal 建立在错误前提上（静态分析仅匹配 `test_runner.py` 文件名，忽略了 `test_harness_runner.py`），无有效子任务可拆解 (预估复杂度：无, 预估 token：0)

### 空转循环历史
- 本 proposal 已在 `openspec/changes/archive/` 中出现 **26+ 次**，全部状态为 skipped/rejected，成功率为 **0%**
- 根因：自演进引擎的测试文件发现逻辑只匹配 `test_{module_basename}.py`（即 `test_runner.py`），不识别 `test_{parent}_{basename}.py` 命名模式（即 `test_harness_runner.py`）
- 建议：修复引擎的测试发现逻辑，而非继续生成此 proposal

## 边界

### IN scope
- 无（前提不成立，无需执行）

### OUT of scope
- 创建 `tests/test_runner.py`（将与已有 `tests/test_harness_runner.py` 完全重复）
- 修改 `zsiga/harness/runner.py` 源码
- 修改已有测试文件 `tests/test_harness_runner.py`

### 依赖的外部条件
- 自演进引擎需修复测试文件发现逻辑（匹配 `test_*_{basename}.py` 模式），否则此 proposal 将持续空转

## 目标

### 成功标准
1. **不创建冗余测试文件** — `tests/test_runner.py` 不应被创建（已有 `tests/test_harness_runner.py` 覆盖）
2. 已有测试全部通过：`python -m pytest tests/test_harness_runner.py` 退出码 0

### 验收方式
- 确认 `tests/test_harness_runner.py` 存在且包含 28 个测试函数
- 确认 `tests/test_runner.py` 不存在（避免冗余）
- 运行 `python -m pytest tests/test_harness_runner.py` 验证已有测试通过

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（源码不可变）
- `tests/test_harness_runner.py`（已有测试不可变）
- `tests/test_harness_conftest.py`（已有 conftest 不可变）

### 项目部署分支
deploy

### 已知风险
- **空转循环风险（已触发 26+ 次）**：引擎会持续为此模块生成 proposal，每次都被 skip/reject，浪费 pipeline 资源
- **静态分析盲区**：引擎只匹配 `test_{basename}.py` 文件名，无法识别 `test_{parent}_{basename}.py` 命名模式，这是系统性缺陷
- **建议修复**：在引擎的测试发现逻辑中增加对 `import` 语句的检查（扫描所有 `test_*.py` 文件中是否 import 了目标模块），而非仅靠文件名匹配

### 预估 token 消耗
- prompt: 0（本 proposal 不应进入实施阶段）
- completion: 0
- 数据来源: 26+ 次空转历史记录
