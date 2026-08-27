# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（317 行，10 个类）补充单元测试覆盖。已有 `tests/test_harness_runner.py`（17 个测试，覆盖 TestStarted/TestPassed/TestFailed/TestError 构造、HarnessResult、discover、run 基本路径），需新建 `tests/test_runner.py` 补充未覆盖的类和方法。

### 拆解后的子任务
- [ ] 1. TestReport / QualificationReport dataclass 测试 (预估复杂度：低, 预估 token：~2000)
  - 覆盖 TestReport 构造、字段默认值、`passed` 联合判定逻辑（`tests_passed == tests_total and errors == 0`）
  - 覆盖 QualificationReport 构造、默认值、`passed` 属性
  - 目标文件：`tests/test_runner.py`（新建）
  - 被测源码：`zsiga/harness/runner.py` 中 TestReport、QualificationReport 类定义

- [ ] 2. HarnessRunner.run_pytest() 方法测试 (预估复杂度：中, 预估 token：~3000)
  - mock `subprocess.run` 隔离外部进程调用，验证 pytest 命令参数拼接、超时处理、非零退出码、stdout/stderr 捕获
  - 验证 JSONL 临时文件写入与读取逻辑
  - 目标文件：`tests/test_runner.py`
  - 被测源码：`zsiga/harness/runner.py` 中 `HarnessRunner.run_pytest()` 方法

- [ ] 3. _HarnessCollectorPlugin pytest hook 测试 (预估复杂度：高, 预估 token：~4000)
  - 构造 mock pytest Item/Report 对象，测试 `pytest_runtest_logreport` hook 对 passed/failed/error 三种报告的处理
  - 验证 JSONL 输出格式（每行一个 JSON 对象，包含 name/outcome/message 字段）
  - 测试 `pytest_collection_modifyitems` 收集逻辑
  - 目标文件：`tests/test_runner.py`
  - 被测源码：`zsiga/harness/runner.py` 中 `_HarnessCollectorPlugin` 类

- [ ] 4. HarnessRunner 边界与集成路径测试 (预估复杂度：中, 预估 token：~3000)
  - 测试 `HarnessRunner` 在空 discover 后调用 run 的行为（应无测试可跑）
  - 测试多文件 discover + run 的时间戳记录
  - 测试 fixtures 参数传递（如 `--timeout`、`-x` 等选项透传到 subprocess）
  - 验证 `HarnessResult` 在各种边界条件下的状态
  - 目标文件：`tests/test_runner.py`
  - 被测源码：`zsiga/harness/runner.py` 中 `HarnessRunner` 类

## 边界

### IN scope
- 新建 `tests/test_runner.py`，包含 ≥4 个 `def test_` 函数
- 覆盖 TestReport、QualificationReport、HarnessRunner.run_pytest()、_HarnessCollectorPlugin、边界集成路径
- 使用 mock 隔离 subprocess、文件 I/O 等外部依赖
- 确保新测试与已有 `tests/test_harness_runner.py` 无冲突

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有的 `tests/test_harness_runner.py`
- 不修改 `zsiga/harness/conftest.py`
- 不涉及 pipeline、agent、daemon 等其他模块

### 依赖的外部条件
- `pytest` 已安装且可运行
- `zsiga/harness/runner.py` 存在且可正常 import
- 已有 `tests/test_harness_runner.py` 中的 fixture 和 import 不与新文件冲突

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在且包含 ≥4 个独立的 `def test_` 函数
2. 每个子任务至少有 1 个对应测试用例覆盖
3. `python -m pytest tests/test_runner.py` 退出码为 0
4. `python -m pytest tests/` 全套测试仍通过（无回归）
5. `ruff check tests/test_runner.py` 无 lint 错误

### 验收方式
- 文件存在性检查：`test -f tests/test_runner.py`
- 符号检查：`grep -c 'def test_' tests/test_runner.py` ≥ 4
- pytest 执行：`python -m pytest tests/test_runner.py -v` 退出码 0
- 全量回归：`python -m pytest tests/ --timeout=60` 退出码 0
- lint 检查：`ruff check tests/test_runner.py` 无输出

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- `tests/test_harness_runner.py`（已有测试，不触碰）
- `zsiga/harness/conftest.py`
- `tests/conftest_zsiga.py`

### 项目部署分支
- main

### 已知风险
- `_HarnessCollectorPlugin` 实现了 pytest hook（`pytest_runtest_logreport`、`pytest_collection_modifyitems`），测试时需构造符合 pytest 内部协议的 mock 对象，接口复杂度较高
- 已有 `tests/test_harness_runner.py` 覆盖了部分 HarnessRunner 功能（discover、run 基本路径），需确保新测试不重复已有覆盖
- pytest-in-pytest 递归风险：`_HarnessCollectorPlugin` 本身是 pytest 插件，在测试中 mock 其 hook 行为时需避免触发真实 pytest 收集

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（基于模块规模 317 行 × 4 个子任务估算）
