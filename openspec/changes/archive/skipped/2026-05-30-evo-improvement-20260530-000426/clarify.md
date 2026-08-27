# clarify.md — add-tests-runner

> ⚠️ **关键纠正**：proposal 声称 `tests/test_runner.py` 不存在需新建，这是错误的。
> `tests/test_harness_runner.py` 已存在（277 行，15 个测试），正确做法是**扩展现有文件**，
> 而非新建 `tests/test_runner.py`（会与现有文件冲突）。

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（352 行）扩展测试覆盖。现有 `tests/test_harness_runner.py`
已覆盖 dataclass 构造、`discover()`、`run()` 的基本路径，但 `run_pytest()` 正常通过路径
和 `_HarnessCollectorPlugin` 的 pytest hook / JSONL 写入行为未直接测试。

### 拆解后的子任务

- [ ] 1. **扩展 `run_pytest()` 正常路径测试** — 在 `tests/test_harness_runner.py` 中新增测试类，
     覆盖 `run_pytest()` 的正常 pass/fail 场景（现有仅测空文件和 collection error）。
     需用 `tmp_path` 创建真实 pytest 测试文件，验证 `HarnessResult` 的 passed/failed/total 字段
     及 `QualificationReport` 结构。
     (预估复杂度：中, 预估 token：~4000 / 无历史参考)

- [ ] 2. **覆盖 `_HarnessCollectorPlugin` pytest hook 行为** — 新增测试验证
     `pytest_runtest_logstart`、`pytest_runtest_logreport` 的 JSONL 输出格式和事件记录。
     通过 `pytester` 或手动构造 hook call 调用 plugin 实例，断言 JSONL 文件内容。
     (预估复杂度：中, 预估 token：~5000 / 无历史参考)

- [ ] 3. **覆盖 `_append_jsonl()` 和 `add_harness_error()` 方法** — 直接实例化
     `_HarnessCollectorPlugin`，调用 `_append_jsonl()` 验证追加写入和 JSON 格式；
     调用 `add_harness_error()` 验证 error 事件被正确记录到 JSONL。
     (预估复杂度：低, 预估 token：~2500 / 无历史参考)

## 边界

### IN scope
- 在现有 `tests/test_harness_runner.py` 中追加新测试类和方法
- 覆盖 `run_pytest()` 正常 pass/fail 路径
- 覆盖 `_HarnessCollectorPlugin` 的 hook 和内部方法
- 使用 `tmp_path` / `pytester` / mock 隔离文件系统依赖

### OUT of scope
- ❌ 不新建 `tests/test_runner.py`（与 `test_harness_runner.py` 冲突）
- ❌ 不修改 `zsiga/harness/runner.py` 源码
- ❌ 不修改 `zsiga/harness/conftest.py`
- ❌ 不重构现有通过的 15 个测试

### 依赖的外部条件
- `pytest` 框架（已安装）
- `pytester` fixture（pytest 内置，用于测试 pytest 插件）
- `zsiga/harness/runner.py` 可正常 import（已确认无 ImportError）

## 目标

### 成功标准
1. `tests/test_harness_runner.py` 中新增 ≥3 个测试方法，覆盖 `run_pytest()` 正常路径、
   `_HarnessCollectorPlugin` hook 行为、`_append_jsonl()` / `add_harness_error()` 方法
2. 所有新增测试独立可运行，不依赖外部服务或运行时环境
3. `python -m pytest tests/test_harness_runner.py` 退出码 0，含新增测试全部通过
4. 不破坏现有 15 个测试（回归率为 0）

### 验收方式
- `python -m pytest tests/test_harness_runner.py -v` 全部通过（退出码 0）
- `ruff check tests/test_harness_runner.py` 无 lint 错误
- `grep -c "def test_" tests/test_harness_runner.py` 输出 ≥18（原 15 + 新增 ≥3）
- 新增测试覆盖了 `run_pytest`、`_HarnessCollectorPlugin`、`_append_jsonl` 三个关键缺口

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py` — 仅读取分析，不修改源码
- `zsiga/harness/conftest.py` — 不修改 harness 配置
- `zsiga/harness/phase_contract.py` — 不影响 phase contract 逻辑
- 所有 `zsiga/` 下的非测试源码文件

### 项目部署分支
- `main`

### 已知风险
- **同名 proposal 循环空转**：`add-tests-runner` 已出现 26+ 次，全部 skip/reject。
  根因是 proposal 模板声称"缺少测试文件"而实际文件已存在。本次 clarify 已纠正此错误前提。
- **pytester 兼容性**：`_HarnessCollectorPlugin` 内部使用 `pytest` hook，测试可能需要
  `pytester` 或 `Testdir` 来模拟 pytest 运行环境，需确认当前 pytest 版本支持。
- **JSONL 文件路径**：`_append_jsonl()` 依赖 `self.jsonl_path`，需在测试中正确设置临时路径。

### 预估 token 消耗
- prompt: ~3000
- completion: ~5000
- 数据来源: 无历史参考（同名 proposal 均未执行到实施阶段）
