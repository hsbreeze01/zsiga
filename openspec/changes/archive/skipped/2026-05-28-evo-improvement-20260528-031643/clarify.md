# clarify.md — add-tests-runner

> **⚠️ 需求工程师批注**：此 proposal 存在多个严重事实性错误，已在下方逐条标注。核心问题：`tests/test_harness_runner.py`（227 行、18 个测试函数）已存在，覆盖了 runner.py 主要公开接口。proposal 声称"缺少测试文件"是误导性的。

## 需求拆解

### 原始需求

为 `zsiga/harness/runner.py`（317 行）添加单元测试覆盖。该模块包含 10 个类（5 个事件 dataclass、HarnessResult、TestReport、QualificationReport、HarnessRunner、_HarnessCollectorPlugin）和 HarnessRunner 的多个方法（`discover()`、`run()`、`_run_file()`、`run_pytest()`、`_append_jsonl()`）。

**关键事实核查**：
- ❌ proposal 声称"函数数: 0" — 实际 HarnessRunner 有 6+ 方法
- ❌ proposal 声称"缺少测试文件" — `tests/test_harness_runner.py` 已存在（227 行，7 个测试类，18 个 def test_）
- ❌ proposal BAC-03 要求"至少 0 个 test_ 函数" — 空文件即可满足
- ❌ proposal BAC-02 用 `test_(待分析)` 占位符 — 不可验证

### 拆解后的子任务

> 以下任务基于 runner.py 实际结构（而非 proposal 错误的"0 函数"分析）和已有测试覆盖缺口重新设计。

- [ ] 1. **分析已有测试覆盖缺口** — 审查 `tests/test_harness_runner.py`（227 行）的实际覆盖范围，对比 `zsiga/harness/runner.py` 全部公开/内部接口，输出缺口清单 (预估复杂度：中, 预估 token：~3000 / 无历史参考)
- [ ] 2. **补充 HarnessRunner 未覆盖方法的测试** — 为已有测试未覆盖的 HarnessRunner 方法（如 `run_pytest()`、`_append_jsonl()`、`_run_file()` 的边界分支）编写测试，追加到 `tests/test_harness_runner.py` 中 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 3. **补充 _HarnessCollectorPlugin 的 pytest hook 测试** — 为 `_HarnessCollectorPlugin` 的 `pytest_collection_modifyitems`、`pytest_runtest_logreport` 等 hook 方法编写 mock pytest session 的单元测试 (预估复杂度：高, 预估 token：~5000 / 无历史参考)

## 边界

### IN scope
- 分析 `tests/test_harness_runner.py` 已有覆盖并识别缺口
- 扩展 `tests/test_harness_runner.py` 添加缺失测试（而非新建 `tests/test_runner.py`）
- 覆盖 HarnessRunner 的 `run_pytest()`、`_append_jsonl()`、`_run_file()` 边界分支
- 覆盖 `_HarnessCollectorPlugin` 的 pytest hook 方法

### OUT of scope
- ❌ 不新建 `tests/test_runner.py`（已有 `test_harness_runner.py` 覆盖，避免重复）
- ❌ 不修改 `zsiga/harness/runner.py` 源码
- ❌ 不修改 `tests/test_harness_runner.py` 中已有的通过测试
- ❌ 不涉及其他 harness 模块（`conftest.py`）

### 依赖的外部条件
- `tests/test_harness_runner.py` 保持现有测试全部通过
- `zsiga/harness/runner.py` 的公开接口在实现期间不发生破坏性变更
- pytest 和 unittest.mock 可用（项目已有依赖）

## 目标

### 成功标准
1. `tests/test_harness_runner.py` 新增测试覆盖了 HarnessRunner 至少 1 个此前未测试的方法
2. `tests/test_harness_runner.py` 新增测试覆盖了 `_HarnessCollectorPlugin` 至少 1 个 hook 方法
3. `python -m pytest tests/test_harness_runner.py` 退出码 0（含新增测试）
4. 新增测试函数数 ≥ 3（每个函数有实际断言，非空 pass）
5. 不引入对 `zsiga/harness/runner.py` 的任何修改

### 验收方式
- `grep -c "def test_" tests/test_harness_runner.py` 输出 ≥ 原有数量 + 3
- `python -m pytest tests/test_harness_runner.py -v` 全部 PASSED
- `git diff zsiga/harness/runner.py` 为空（零修改）
- 新增测试中包含有意义的 `assert` 语句（非 `assert True` 等无效断言）

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py` — 仅读取分析，不修改
- `tests/test_harness_runner.py` 中已有的测试代码 — 只追加，不修改

### 项目部署分支
- main

### 已知风险
- **已有测试文件冲突**：proposal 指定新建 `tests/test_runner.py`，但 `tests/test_harness_runner.py` 已存在且覆盖了同一模块。新建文件会导致命名混乱和覆盖度假象。本 clarify.md 已将方案调整为扩展已有文件。
- **_HarnessCollectorPlugin 测试复杂度高**：该类实现了 pytest hook，测试需要 mock pytest session 对象（`Session`、`Item`、`TestReport`），构造测试数据较复杂
- **自演进引擎生成质量低**：proposal 的静态分析数据严重失真（声称 0 函数、测试名用占位符），后续自演进 proposal 需增强事实核查
- **历史 REJECT/PUSHBACK 记录**：此 proposal 模式已被拒绝多次（见 session history），执行前需确认与已有测试不重复

### 预估 token 消耗
- prompt: ~8000（需读取 runner.py 全文 + 已有测试文件 + 编写新测试）
- completion: ~6000（新增 3-8 个测试函数含 mock 设置）
- 数据来源: 无历史参考（同类 proposal 从未成功执行）
