# clarify.md — add-tests-runner

> ⚠️ **需求工程师重大风险提示**：此 proposal 的核心前提需要严格审查。
> proposal 声称 `zsiga/harness/runner.py` "缺少测试文件"，但代码库中已有
> **至少 4 个测试文件**覆盖该模块（详见约束节）。BAC 含占位符文本且最低测试数为 0，
> 验收标准形同虚设。以下拆解基于 proposal 原始意图 + 实际代码状态进行修正性分析。

---

## 需求拆解

### 原始需求

为模块 `zsiga/harness/runner.py`（317 行，含 10 个类）添加单元测试覆盖。proposal 的
静态分析声称"0 函数、10 类、无高 CC 函数"，但实际模块包含 `HarnessRunner`（含
`discover()`/`run()`/`_run_file()`/`run_pytest()` 等方法）和
`_HarnessCollectorPlugin`（含 pytest hook 方法）等有复杂行为的类。

### 拆解后的子任务

- [ ] 1. **识别现有测试覆盖缺口** — 审计 `tests/test_harness_runner.py`（227行）及
  3 个同 change ID 的 spec 测试文件，列出 `runner.py` 中尚未被覆盖的类/方法/分支。
  （预估复杂度：中，预估 token：~3000）

- [ ] 2. **为缺口区域编写测试** — 仅针对已确认未覆盖的类方法或分支编写新测试，
  避免与现有测试重复。覆盖目标包括但不限于：`HarnessRunner._run_file()` 的
  AssertionError vs 其他 Exception 分支、`HarnessRunner.results` 属性、
  `_HarnessCollectorPlugin` 的 pytest hook 行为。
  （预估复杂度：中，预估 token：~5000）

- [ ] 3. **验收与回归** — 确保所有新增测试通过 `pytest`，且不破坏现有测试。
  `ruff check` 无新增 lint 问题。
  （预估复杂度：低，预估 token：~1000）

---

## 边界

### IN scope

- 分析 `zsiga/harness/runner.py` 的实际覆盖缺口
- 在 `tests/` 目录下编写补充测试（文件名需与已有测试协调，避免冲突）
- 使用 mock 隔离外部依赖（subprocess、文件 I/O）

### OUT of scope

- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有的 `tests/test_harness_runner.py` 及 3 个 spec 测试文件
- 不创建与已有测试功能重叠的测试用例

### 依赖的外部条件

- `zsiga/harness/runner.py` 源码结构稳定（当前 317 行，10 个类）
- `tests/test_harness_runner.py`（227 行）及 3 个同 change ID spec 测试文件已存在且通过
- pytest 框架及 `tests/conftest_zsiga.py` fixture 可用

---

## 目标

### 成功标准

1. **增量覆盖有价值** — 新增测试覆盖了 `runner.py` 中此前未被任何测试文件触及的
   类方法或分支路径，且不与现有测试功能重叠
2. **全量通过** — `python -m pytest tests/ -x` 退出码 0，无回归
3. **代码质量** — 新增测试文件 `ruff check` 无错误

### 验收方式

- `pytest` 执行新增测试文件，全部 PASS
- 人工审查新增测试不与 `test_harness_runner.py` 及 3 个 spec 测试文件内容重复
- `ruff check` 通过

> **注意**：原始 BAC 不可直接采用——BAC-02 含占位符 `test_(待分析)`，
> BAC-03 要求"至少 0 个 `def test_`"（空文件即可满足）。以上验收方式为修正后版本。

---

## 约束

### 不能修改的文件

- `zsiga/harness/runner.py`（源码只读）
- `tests/test_harness_runner.py`（已有 227 行覆盖）
- `tests/test_spec_evo_improvement_20260528_110555__runner_gap_coverage.py`
- `tests/test_spec_evo_improvement_20260528_110555__runner_pytest_integration.py`
- `tests/test_spec_evo_improvement_20260528_110555__runner_report_dataclasses.py`

### 项目部署分支

- `main`（默认分支）

### 已知风险

1. **核心前提可能不成立** — proposal 声称模块"缺少测试文件"，但已有 4 个测试文件
   覆盖该模块。如果缺口分析结果显示现有覆盖已充分，此 proposal 的全部工作可能
   不产生增量价值
2. **BAC 质量极差** — BAC-02 使用字面占位符 `test_(待分析)`，BAC-03 最低门槛为 0，
   验收标准无法约束实际交付质量。需以修正后验收方式为准
3. **静态分析数据不可信** — 声称"函数数: 0"、类 methods=[]，但 `HarnessRunner`
   有 `discover()`、`run()`、`_run_file()`、`run_pytest()` 等方法。任何执行决策
   必须基于实际代码审查，不可依赖 proposal 中的静态分析数据
4. **自演进引擎生成** — 此 proposal 由自演进引擎自动生成，历史同类 proposal
   （`verify-layer0-with-tests`）在 verify 阶段失败过

### 预估 token 消耗

- prompt: ~8000（含代码读取 + 覆盖缺口审计）
- completion: ~4000（缺口分析 + 测试编写 + 验证）
- 数据来源: 无历史参考（同类 proposal 历史上被 REJECT/PUSHBACK，无成功执行记录）
