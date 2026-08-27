# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（317 行，10 个类）补充单元测试，新建 `tests/test_runner.py`。
已有 `tests/test_harness_runner.py`（17 个测试）覆盖了事件 dataclass 构造、HarnessResult、HarnessRunner.discover() 和 HarnessRunner.run() 的基本路径。
`tests/test_runner.py` 需覆盖**尚未被 test_harness_runner.py 覆盖的公开类和方法**，避免重复。

### 拆解后的子任务

- [ ] 1. **TestReport / QualificationReport dataclass 测试** — 覆盖 TestReport 字段默认值/自定义值、QualificationReport 组合逻辑 (预估复杂度：低, 预估 token：~2500)
- [ ] 2. **HarnessRunner.__init__ 与 run_pytest() 方法测试** — 覆盖 fixtures 参数传递、run_pytest() 调用 _run_file() 的成功/失败路径、mock subprocess/pytest.main (预估复杂度：中, 预估 token：~4000)
- [ ] 3. **HarnessRunner._run_file() 边界路径测试** — 覆盖模块加载失败、测试收集异常、超时等边界场景 (预估复杂度：中, 预估 token：~3500)
- [ ] 4. **_HarnessCollectorPlugin 内部插件测试** — 覆盖 pytest_collection_modifyitems 钩子、事件收集到 HarnessResult 的转换逻辑（需 mock pytest session/items）(预估复杂度：中, 预估 token：~4000)

## 边界

### IN scope
- 新建 `tests/test_runner.py`，为 runner.py 中未被 test_harness_runner.py 覆盖的类/方法编写单元测试
- 覆盖目标：TestReport、QualificationReport、HarnessRunner.run_pytest()、HarnessRunner._run_file()、_HarnessCollectorPlugin
- 使用 mock 隔离 pytest.main()、subprocess、文件 I/O 等外部依赖
- 确保 ruff check 通过

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有的 `tests/test_harness_runner.py`
- 不重复覆盖 test_harness_runner.py 已测试的事件 dataclass（TestEvent/TestStarted/TestPassed/TestFailed/TestError）、HarnessResult、HarnessRunner.discover()、HarnessRunner.run() 基本路径

### 依赖的外部条件
- `zsiga/harness/runner.py` 保持当前结构不变（10 个类，公开接口稳定）
- `tests/test_harness_runner.py` 继续存在且通过（不产生命名冲突）
- pytest 可正常运行（测试框架可用）

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在且包含 ≥ 3 个 `def test_` 函数（非占位符命名）
2. 所有测试函数名语义明确，反映被测行为（如 `test_run_pytest_success`、`test_report_defaults`、`test_collector_plugin_modifies_items`）
3. `python -m pytest tests/test_runner.py` 退出码 0
4. `ruff check tests/test_runner.py` 无错误
5. 实际覆盖 TestReport、QualificationReport、run_pytest()、_run_file()、_HarnessCollectorPlugin 中至少 3 个

### 验收方式
- `ls tests/test_runner.py` 确认文件存在
- `grep -c 'def test_' tests/test_runner.py` 确认 ≥ 3 个测试函数
- `python -m pytest tests/test_runner.py -v` 确认全部通过
- `ruff check tests/test_runner.py` 确认无 lint 错误
- 代码审查确认无与 test_harness_runner.py 的重复覆盖

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py` — 仅读取分析
- `tests/test_harness_runner.py` — 不修改已有测试
- `tests/conftest.py` / `tests/conftest_zsiga.py` — 不修改全局 conftest

### 项目部署分支
- main

### 已知风险
- **pytest-in-pytest 递归**：_HarnessCollectorPlugin 内部调用 pytest.main()，测试时必须严格 mock，否则会触发 pytest 递归执行
- **命名冲突**：已有 test_harness_runner.py，需确保 test_runner.py 中的测试不与前者重复（通过 grep 已有测试函数名确认）
- **proposal 原始 BAC 质量低**：原始 BAC-02（`test_(待分析)`）和 BAC-03（"至少 0 个"）是无效占位符，本 clarify.md 已修正为具体标准
- **HarnessRunner._run_file 依赖真实文件系统**：需要用 tmpdir 或 mock 隔离

### 预估 token 消耗
- prompt: ~14000
- completion: ~6000
- 数据来源: historical（参考 test_harness_runner.py 的 17 个测试 ≈ 350 行代码规模）
