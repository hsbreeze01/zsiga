# clarify.md — add-tests-runner

> **⚠️ 前提校验失败 — 建议 REJECT**
>
> Proposal 声称 `zsiga/harness/runner.py` "缺少测试文件 `tests/test_runner.py`"，但 `tests/test_harness_runner.py`（277 行，20+ 个 `def test_`）已完整覆盖该模块全部 10 个公开类。这是一个由引擎 basename 匹配 bug（`runner` ≠ `harness_runner`）导致的空转循环 proposal，已被生成 27+ 次并全部 skip/reject。以下需求拆解仅作为结构化记录，**不建议执行**。

---

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（352 行, 10 个类）添加单元测试文件 `tests/test_runner.py`，覆盖公开符号，确保 pytest 通过。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_runner.py`，导入 `zsiga.harness.runner` 全部公开符号并编写冒烟测试（`test_module_import`, `test_module_smoke`）（预估复杂度：低, 预估 token：~1500 / 无历史参考 — 同类 proposal 27+ 次全部失败）
- [ ] 2. 为 runner.py 的 dataclass 族（TestEvent/TestStarted/TestPassed/TestFailed/TestError）补充构造和字段断言测试（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 3. 为 HarnessResult / TestReport / QualificationReport 编写聚合逻辑测试（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 4. 为 HarnessRunner 核心方法（discover / run / run_pytest）编写 mock 隔离测试（预估复杂度：中, 预估 token：~3000 / 无历史参考）

---

## 边界

### IN scope
- 创建 `tests/test_runner.py`（新建文件）
- 覆盖 `zsiga/harness/runner.py` 的公开符号

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有测试文件 `tests/test_harness_runner.py`
- 不修复引擎 basename 匹配 bug（`zsiga/intake/evolution.py` L1080-1087）

### 依赖的外部条件
- `zsiga/harness/runner.py` 保持当前 API 不变
- 项目 pytest 配置可发现新测试文件

### ⚠️ 重叠警告
`tests/test_harness_runner.py` 已存在并覆盖了全部 10 个公开类（TestEventDataclasses 4 tests、TestHarnessResult 2 tests、TestHarnessRunnerDiscover 3 tests、TestHarnessRunnerRun 7 tests、TestHarnessRunnerPytestFailClosed 4 tests）。本 proposal 的全部产出将与已有测试**功能重叠**，不会增加实质性覆盖率。

---

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在
2. 文件包含 `test_module_import` 和 `test_module_smoke` 函数
3. 文件包含至少 1 个 `def test_` 函数
4. `python -m pytest tests/test_runner.py` 退出码 0

### 验收方式
- `ls tests/test_runner.py` 确认文件存在
- `grep -c 'def test_' tests/test_runner.py` 确认测试函数数量
- `python -m pytest tests/test_runner.py -v` 确认全部通过

### ⚠️ 质量评估
即使全部 BAC 通过，产出文件 `tests/test_runner.py` 将与已有 `tests/test_harness_runner.py`（277 行，20+ 测试）高度重叠，属于低价值冗余产出。

---

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`
- `tests/test_harness_runner.py`
- `zsiga/intake/evolution.py`（根因所在，但 out of scope）

### 项目部署分支
- deploy（zsiga 自演进目标）

### 已知风险
1. **空转循环**：此 proposal 已被自演进引擎生成 27+ 次（2026-05-26 ~ 2026-05-30），全部被 skip/reject，成功率 0%。继续执行不会打破循环。
2. **根因未修复**：即使本次执行成功，引擎仍会因 basename 匹配 bug（`runner` ≠ `harness_runner`）反复生成同名 proposal。真正需要的修复是 `zsiga/intake/evolution.py` L1080-1087 的匹配逻辑。
3. **虚假前提**：Proposal 声称"0 函数"，但 HarnessRunner 有 `discover()`/`run()`/`run_pytest()` 等方法；声称"缺少测试"，但已有 20+ 测试覆盖全部公开 API。静态分析数据严重失真。
4. **BAC 可通过但无价值**：4 条 BAC 全部为低门槛检查（文件存在 + 2 个冒烟测试 + pytest 通过），即使全部满足也不代表有意义的增量。

### 预估 token 消耗
- prompt: ~2000
- completion: ~2500
- 数据来源: 无历史参考（同类 proposal 无成功执行记录）
