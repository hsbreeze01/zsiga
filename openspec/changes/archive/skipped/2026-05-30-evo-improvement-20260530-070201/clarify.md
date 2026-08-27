# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（352 行，10 个类）添加单元测试文件 `tests/test_runner.py`，覆盖公开函数与类。

### ⚠️ 前提验证失败（致命）

**此 proposal 的核心前提为假，不应执行。** 以下是事实核查：

| 声明 | 实际 | 判定 |
|------|------|------|
| "缺少测试文件 `tests/test_runner.py`" | `tests/test_harness_runner.py` **已存在**（277 行，28 个 `def test_` 函数） | ❌ 文件名启发式匹配失败 |
| "0 函数" | 模块含 2 个核心类（`HarnessRunner`、`_HarnessCollectorPlugin`），各有多个方法 | ❌ 静态分析数据失真 |
| "无测试覆盖" | 已覆盖：TestEventDataclasses(4)、TestHarnessResult(2)、TestHarnessRunnerDiscover(3)、TestHarnessRunnerRun(7)、TestHarnessRunnerPytestFailClosed(4) | ❌ 完全不符合事实 |

**已有测试文件覆盖矩阵：**

| 目标类 | 测试类 | 测试数 |
|--------|--------|--------|
| TestStarted/Passed/Failed/Error | `TestEventDataclasses` | 4 |
| HarnessResult | `TestHarnessResult` | 2 |
| HarnessRunner.discover() | `TestHarnessRunnerDiscover` | 3 |
| HarnessRunner.run() | `TestHarnessRunnerRun` | 7 |
| HarnessRunner.run_pytest() | `TestHarnessRunnerPytestFailClosed` | 4 |
| QualificationReport/TestReport | 同上 | 2 |

### 拆解后的子任务

> 以下子任务仅在忽略前提验证失败时才有意义。实际建议：**不执行任何子任务**。

- [ ] 1. 创建 `tests/test_runner.py` 并编写导入冒烟测试 (预估复杂度：低, 预估 token：~1500)
- [ ] 2. 为事件 dataclass 族（TestEvent/TestStarted/TestPassed/TestFailed/TestError）编写构造与字段测试 (预估复杂度：低, 预估 token：~2000)
- [ ] 3. 为 HarnessResult/TestReport/QualificationReport 编写聚合逻辑测试 (预估复杂度：低, 预估 token：~2000)
- [ ] 4. 为 HarnessRunner（discover/run/run_pytest）编写 mock 隔离测试 (预估复杂度：中, 预估 token：~4000)

> **注意**：以上所有子任务与 `tests/test_harness_runner.py` 现有测试**完全重叠**。

## 边界

### IN scope
- 创建 `tests/test_runner.py`（与 `tests/test_harness_runner.py` 功能重叠）

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码（proposal 明确声明）

### 依赖的外部条件
- `zsiga/harness/runner.py` 存在且可导入（✅ 已确认）
- `pytest` 可用（✅ 项目标准依赖）
- **⚠️ 前提条件未满足**：目标模块需确认无现有测试覆盖 — 实际已有覆盖

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在（但与 `tests/test_harness_runner.py` 冗余）
2. 包含 `test_module_import`、`test_module_smoke` 函数
3. `python -m pytest tests/test_runner.py` 退出码 0

### 验收方式
- 文件存在性检查：`test -f tests/test_runner.py`
- 函数存在性检查：`grep -c 'def test_' tests/test_runner.py`
- 测试通过：`python -m pytest tests/test_runner.py`
- **⚠️ 缺失验收**：无检查与已有测试文件 `tests/test_harness_runner.py` 的重叠率

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`
- `tests/test_harness_runner.py`（已有 277 行完整测试覆盖）

### 项目部署分支
- （未在 proposal 中指定，需确认）

### 已知风险
1. **🔴 致命：重复测试文件** — 创建 `tests/test_runner.py` 会与 `tests/test_harness_runner.py`（277 行，28 个测试）产生完全重叠，制造维护负担而非价值
2. **🔴 致命：空转循环** — 同名 proposal 已循环 26+ 次（2026-05-27 ~ 2026-05-30），全部 skip/reject，成功率 0%
3. **🟡 根因未解决** — 自演进引擎使用 `test_{module_basename}.py` 启发式匹配（即 `test_runner.py`），无法发现 `test_harness_runner.py`（路径命名约定），导致永远认为该模块无测试
4. **🟡 静态分析数据失真** — 声称"0 函数"但实际有 `HarnessRunner.discover()`、`HarnessRunner.run()`、`HarnessRunner.run_pytest()` 等方法

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（同类 proposal 从未通过执行阶段）

### 💡 建议替代方案

不执行此 proposal，而是修复自演进引擎的测试发现逻辑：
- 扫描所有 `test_*.py` 文件中的 `import` 语句来识别覆盖关系
- 支持 `test_{parent}_{basename}.py` 命名模式（如 `test_harness_runner.py` 对应 `zsiga/harness/runner.py`）
- 将 `add-tests-runner` 加入 proposal 黑名单
