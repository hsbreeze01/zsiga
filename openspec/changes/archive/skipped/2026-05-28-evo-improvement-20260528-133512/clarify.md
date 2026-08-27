# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py` 补充单元测试覆盖。该模块（317 行）包含 10 个类：5 个事件 dataclass（`TestEvent`/`TestStarted`/`TestPassed`/`TestFailed`/`TestError`）、`TestReport`、`QualificationReport`、`HarnessResult`、`HarnessRunner`（含 `discover()`/`run()`/`run_pytest()` 等方法）、`_HarnessCollectorPlugin`（pytest hook 实现）。

**关键事实修正**：proposal 声称"无测试"，但 `tests/test_harness_runner.py`（227 行，16 个 test）已覆盖事件 dataclass、`HarnessResult`、`HarnessRunner.discover()` 和 `HarnessRunner.run()`。本次变更聚焦于 **剩余覆盖缺口**。

### 拆解后的子任务

- [ ] 1. **TestReport / QualificationReport dataclass 覆盖** — 验证 `tests/test_spec_evo_improvement_20260528_133512__report_dataclass_coverage.py` 正确覆盖两个字段的构造、字段访问、`__test__ = False` 标记、空列表边界 (预估复杂度：低, 预估 token：~2000)
- [ ] 2. **HarnessRunner.run_pytest() 集成测试** — 验证 `tests/test_spec_evo_improvement_20260528_133512__run_pytest_coverage.py` 覆盖 passing/failing test file 场景、JSONL 输出文件写入（每行合法 JSON 含 name/status/duration_s/message/timestamp）(预估复杂度：中, 预估 token：~3000)
- [ ] 3. **_HarnessCollectorPlugin hook 单元测试** — 验证 `tests/test_spec_evo_improvement_20260528_133512__runner_coverage_gaps.py` 覆盖 `pytest_runtest_logstart`（记录开始时间）、`pytest_runtest_logreport`（setup/call/teardown 分发，call 阶段 passed/failed/error 三路分支）、`_append_jsonl` 单行/多行写入 (预估复杂度：中, 预估 token：~3000)
- [ ] 4. **全量测试通过验证** — 运行 `pytest tests/test_spec_evo_improvement_20260528_133512__*.py` 及 `pytest tests/test_harness_runner.py`，确保全部通过且无回归 (预估复杂度：低, 预估 token：~1000)

## 边界

### IN scope
- 验证/补全 3 个新增 spec 测试文件的内容和正确性
- 覆盖 `TestReport`、`QualificationReport` dataclass
- 覆盖 `HarnessRunner.run_pytest()` 公开方法
- 覆盖 `_HarnessCollectorPlugin` 内部插件（`pytest_runtest_logstart`、`pytest_runtest_logreport`、`_append_jsonl`）
- 确保新增测试与已有 `tests/test_harness_runner.py` 不冲突

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不创建 `tests/test_runner.py`（proposal 原始目标文件名有误，实际测试已分布在 spec 测试文件中）
- 不重复覆盖已有测试的事件 dataclass（TestEvent/TestStarted/TestPassed/TestFailed/TestError）和 HarnessResult
- 不覆盖 `HarnessRunner.discover()` / `HarnessRunner.run()`（已在 `test_harness_runner.py` 中充分覆盖）

### 依赖的外部条件
- pytest 框架可用（项目已配置）
- `zsiga/harness/runner.py` 源码结构稳定
- `tmp_path` fixture 用于临时测试文件和 JSONL 输出

## 目标

### 成功标准
1. 3 个 spec 测试文件均存在且包含实质性测试（非空文件）
2. `TestReport` 和 `QualificationReport` 的构造、字段访问、`__test__` 标记有明确断言
3. `run_pytest()` 的 passing/failing 场景及 JSONL 写入有集成测试覆盖
4. `_HarnessCollectorPlugin` 的 3 个 hook 方法（logstart/logreport/append_jsonl）有单元测试覆盖
5. 全部新增测试 + 已有 `test_harness_runner.py` 通过 pytest，退出码 0
6. ruff check 无新增 lint 问题

### 验收方式
- `python -m pytest tests/test_spec_evo_improvement_20260528_133512__*.py -v` 退出码 0
- `python -m pytest tests/test_harness_runner.py -v` 退出码 0（无回归）
- `ruff check tests/test_spec_evo_improvement_20260528_133512__*.py` 无错误
- 人工审查测试断言覆盖了上述成功标准中的关键路径

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- `tests/test_harness_runner.py`（已有测试，不侵入）

### 项目部署分支
- main

### 已知风险
- proposal 原始 BAC 质量极差（占位符 `test_(待分析)`、最少 0 个测试函数），需以实际覆盖缺口为准而非 BAC 字面要求
- proposal 建议创建 `tests/test_runner.py`，但测试已通过 spec 命名约定分布在 3 个文件中，不应再创建冗余文件
- 已有 10+ 个同名 `add-tests-runner` 提案被否决，需确保本次交付有实质增量覆盖而非重复

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考（基于已有 spec 测试文件内容推断）
