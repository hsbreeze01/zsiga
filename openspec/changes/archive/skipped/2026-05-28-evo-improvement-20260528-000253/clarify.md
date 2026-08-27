# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
为无测试模块 `zsiga/harness/runner.py`（317 行，10 个类）添加单元测试覆盖。该模块包含测试事件数据类（TestEvent 家族）、报告模型（TestReport/QualificationReport）、核心运行器（HarnessRunner）和 pytest 插件（_HarnessCollectorPlugin）。

**现状修正**：proposal 原始 BAC 存在严重缺陷（BAC-02 使用占位符 `test_(待分析)`，BAC-03 要求"至少 0 个测试函数"——空文件即可通过）。本 clarify 重写验收标准并按功能模块拆分任务。

**已有覆盖**：项目中已存在 `tests/test_harness_runner.py`（17 个测试）和本 change 下 5 个 spec 测试文件。本 clarify 基于实际已实施内容校准。

### 拆解后的子任务

- [ ] 1. 数据类与事件模型测试 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 覆盖 `TestEvent`、`TestStarted`、`TestPassed`、`TestFailed`、`TestError` 的构造、默认值、`__test__=False` 标记
  - 覆盖 `HarnessResult`、`TestReport`、`QualificationReport` 的构造与 `passed` 属性逻辑
  - 文件范围：`tests/test_spec_evo_improvement_20260528_000253__runner_report_dataclasses.py`、`tests/test_spec_evo_improvement_20260528_000253__runner_report_models.py`

- [ ] 2. HarnessRunner 核心逻辑测试 (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 覆盖 `HarnessRunner.__init__` 参数校验与 fixture 注入
  - 覆盖 `discover()` 测试文件发现与排序
  - 覆盖 `_run_file()` 边界情况（文件不存在、subprocess 失败）
  - 文件范围：`tests/test_spec_evo_improvement_20260528_000253__runner_harness_core.py`

- [ ] 3. _HarnessCollectorPlugin 与 pytest 集成测试 (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 覆盖 `_HarnessCollectorPlugin` 的 pytest hook 方法（`pytest_runtest_logstart`、`pytest_runtest_logreport`）
  - 覆盖 `_append_jsonl()` JSONL 持久化输出格式
  - 覆盖 `run_pytest()` 端到端调用（mock subprocess）
  - 文件范围：`tests/test_spec_evo_improvement_20260528_000253__runner_plugin_and_init.py`、`tests/test_spec_evo_improvement_20260528_000253__runner_pytest_integration.py`

## 边界

### IN scope
- 为 `zsiga/harness/runner.py` 的 10 个类编写单元测试
- 使用 mock 隔离 subprocess、文件 I/O 等外部依赖
- 测试可独立运行，不依赖运行时环境或真实 LLM 调用

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改 `zsiga/harness/conftest.py` 或 `zsiga/harness/capability/` 下的任何文件
- 不涉及其他模块（config、daemon、pipeline 等）的测试
- 不创建单一的 `tests/test_runner.py`（已采用 spec 测试文件命名规范分散覆盖）

### 依赖的外部条件
- `pytest` 可正常运行（项目已有 100+ 测试文件，pytest 环境已就绪）
- `zsiga/harness/runner.py` 源码无 lint 错误（proposal 确认 ruff 0 issues）

## 目标

### 成功标准
1. 本 change 下存在至少 4 个 spec 测试文件覆盖 runner.py 的不同功能模块
2. 所有 spec 测试文件合计包含至少 25 个 `def test_` 函数
3. `python -m pytest tests/test_spec_evo_improvement_20260528_000253__runner_*.py` 退出码 0
4. 覆盖 runner.py 全部 10 个类中的至少 8 个（TestEvent、TestStarted、TestPassed、TestFailed、TestError、HarnessResult、TestReport、HarnessRunner）

### 验收方式
- `ls tests/test_spec_evo_improvement_20260528_000253__runner_*.py | wc -l` ≥ 4
- `grep -r 'def test_' tests/test_spec_evo_improvement_20260528_000253__runner_*.py | wc -l` ≥ 25
- `python -m pytest tests/test_spec_evo_improvement_20260528_000253__runner_*.py -x` 退出码 0
- 已有测试 `tests/test_harness_runner.py` 仍全部通过（无回归）

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（只读分析）
- `zsiga/harness/conftest.py`
- `zsiga/harness/capability/` 下所有文件
- `tests/test_harness_runner.py`（已有 17 个测试，不得破坏）

### 项目部署分支
- main

### 已知风险
- `_HarnessCollectorPlugin` 实现了 pytest hook 接口，测试时需 mock `pytest.TestReport` 对象，若 mock 不精确可能引入假阳性
- `HarnessRunner.run_pytest()` 内部调用 subprocess 启动 pytest 进程，存在 pytest-in-pytest 递归风险，必须 mock subprocess
- runner.py 中的类名以 `Test` 开头（TestEvent、TestStarted 等），pytest 默认会收集它们为测试类——这些类已标记 `__test__=False`，但测试中需确认该标记生效

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（基于 5 个已存在 spec 测试文件的体量估算）
