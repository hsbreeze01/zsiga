# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
Proposal 要求为 `zsiga/harness/runner.py`（317 行）创建 `tests/test_runner.py` 单元测试文件。该 proposal 由自演进引擎生成，声称该模块"缺少测试文件"。

**⚠️ 关键事实冲突**：经过并行探索确认，`tests/test_harness_runner.py` **已存在**（227 行），包含 6 个测试类、约 16 个 `def test_` 函数，覆盖了该模块的核心公开接口：
- `TestEventDataclasses`（4 个测试）— TestStarted/Passed/Failed/Error 数据类构造与字段
- `TestHarnessResult`（2 个测试）— 默认值与自定义值
- `TestHarnessRunnerDiscover`（3 个测试）— discover() 文件发现、空目录、不存在目录
- `TestHarnessRunnerRun`（7 个测试）— run() pass/fail/error 三路分支、多文件、results 属性、无 discovery、时间戳

Proposal 的静态分析存在多处错误：
- 声称"函数数: 0"，实际 HarnessRunner 有 discover()/run()/_run_file()/run_pytest()/_append_jsonl() 等方法
- 仅列出 5/10 个类，遗漏 HarnessResult、HarnessRunner、_HarnessCollectorPlugin、TestReport、QualificationReport
- BAC-02 使用占位符 `test_(待分析)`，BAC-03 要求"至少 0 个 test 函数"（空文件即可满足）

### 拆解后的子任务

鉴于已有测试文件覆盖了主要公开接口，以下任务聚焦于 **尚未被 `test_harness_runner.py` 覆盖的真实缺口**：

- [ ] 1. **分析 runner.py 已有测试覆盖缺口** — 对比 `runner.py` 全部 10 个类的方法与 `test_harness_runner.py` 的 16 个测试，识别未覆盖的类/方法/分支（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **为未覆盖的公开接口补充测试** — 重点覆盖 `_HarnessCollectorPlugin`（pytest hook 方法 `pytest_collection_modifyitems`/`pytest_runtest_logreport`/`pytest_sessionfinish`）、`HarnessRunner.results` 属性、`HarnessRunner._run_file()` 的错误路径（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 3. **验证所有测试通过** — 运行 `python -m pytest tests/test_harness_runner.py` 确认退出码 0，运行 ruff 确认无 lint 问题（预估复杂度：低, 预估 token：~1000 / 无历史参考）

## 边界

### IN scope
- 扩展 `tests/test_harness_runner.py` 中已有的测试，或确认新建文件不与已有测试重复
- 覆盖 `zsiga/harness/runner.py` 中尚未被测试的类和方法（特别是 `_HarnessCollectorPlugin`、`HarnessRunner._run_file()` 边界情况）
- 确保新增测试可独立运行，不依赖运行时环境

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改 `tests/test_harness_runner.py` 中已有的通过测试
- 不涉及 pipeline 自身代码或 proposal gate 逻辑
- 不创建与已有测试重复的测试用例

### 依赖的外部条件
- `zsiga/harness/runner.py` 保持当前接口不变
- pytest 基础设施正常（`conftest_zsiga.py`、`tmp_path` fixture 可用）
- 已有测试 `test_harness_runner.py` 全部通过（基线健康）

## 目标

### 成功标准
1. `zsiga/harness/runner.py` 中此前未覆盖的公开方法（至少 `_HarnessCollectorPlugin` 的 pytest hook 方法）有对应的 `def test_` 测试函数
2. 新增测试与已有 `test_harness_runner.py` 无逻辑重复
3. 全部测试（已有 + 新增）通过 pytest，退出码 0
4. ruff check 无新增 lint 问题

### 验收方式
- 运行 `python -m pytest tests/test_harness_runner.py -v` 检查新增测试通过
- 人工审查确认无与已有测试重复的断言逻辑
- 运行 `ruff check tests/test_harness_runner.py` 确认无问题

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- `tests/test_harness_runner.py` 中已有的测试函数（可追加新测试类/函数，不修改已有代码）

### 项目部署分支
- main（当前工作分支）

### 已知风险
- **proposal 前提部分虚假**：声称模块"缺少测试文件"，实际已有完善覆盖。盲目创建 `tests/test_runner.py` 会产生冗余文件，应扩展已有 `test_harness_runner.py` 或确保新文件不重复
- **BAC 质量极差**：BAC-02 用占位符 `test_(待分析)`，BAC-03 要求"至少 0 个测试函数"——空文件即可通过。需以实际覆盖率为目标而非字面 BAC
- **_HarnessCollectorPlugin 测试复杂度高**：该类实现了 pytest hook，测试时可能需要 mock pytest session 对象，存在 pytest-in-pytest 递归风险
- **自演进引擎生成**：此 proposal 由自演进引擎自动生成，静态分析数据严重失真（0 函数、仅 5/10 类），需求拆解需以实际代码为准

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类 proposal 均被 proposal gate REJECT/PUSHBACK，无成功执行记录）
