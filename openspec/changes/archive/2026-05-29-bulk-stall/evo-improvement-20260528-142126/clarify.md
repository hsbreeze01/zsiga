# clarify.md — add-tests-runner

> **⚠ 前提校正**：proposal 声称 `zsiga/harness/runner.py` "缺少测试文件"，但 `tests/test_harness_runner.py`（227 行、15 个 test）已存在并覆盖了主要公开 API。本需求契约聚焦于**现有测试的实际缺口**，而非从零创建。

## 需求拆解

### 原始需求
Proposal 要求为 `zsiga/harness/runner.py`（317 行、10 个类）创建 `tests/test_runner.py`。经事实核查，已有 `tests/test_harness_runner.py` 覆盖了 4 个事件 dataclass、`HarnessResult`、`HarnessRunner.discover()`（3 场景）、`HarnessRunner.run()`（8 场景）。**真正缺失的覆盖**是 `run_pytest()`、`_HarnessCollectorPlugin`（pytest hook + JSONL 写入）、`TestReport`、`QualificationReport` 四个区域。

### 拆解后的子任务

- [ ] 1. **扩展 `tests/test_harness_runner.py`：覆盖 `TestReport` 和 `QualificationReport` dataclass**  
  验证 `TestReport`（L82）的各字段默认值与自定义值、`QualificationReport`（L93）的聚合逻辑。这两个 dataclass 在现有测试中未被独立测试。  
  （预估复杂度：低, 预估 token：~1500）

- [ ] 2. **扩展 `tests/test_harness_runner.py`：覆盖 `HarnessRunner.run_pytest()` 方法**  
  `run_pytest()`（L169）通过 `pytest.main()` 执行单个测试文件并返回 `TestReport` 列表。需测试：正常通过、断言失败、异常中断、空文件、收集失败等路径。使用 `tmp_path` 创建临时测试文件 + mock `pytest.main` 或直接调用。  
  （预估复杂度：中, 预估 token：~3000）

- [ ] 3. **扩展 `tests/test_harness_runner.py`：覆盖 `_HarnessCollectorPlugin` pytest hook 与 JSONL 输出**  
  `_HarnessCollectorPlugin`（L269）实现了 `pytest_runtest_logstart`、`pytest_runtest_logreport`，收集 `TestReport` 并通过 `_append_jsonl()` 写入 JSONL 文件。需测试：hook 对 pass/fail/error 三种 report 的处理、JSONL 追加写入、多个测试结果的累积。  
  （预估复杂度：中, 预估 token：~3000）

## 边界

### IN scope
- 在 `tests/test_harness_runner.py` 中**追加**测试类和测试函数，覆盖上述 3 个缺口区域
- 测试 `TestReport`、`QualificationReport` 的字段和默认值
- 测试 `HarnessRunner.run_pytest()` 的主要分支（pass / fail / error / 空文件）
- 测试 `_HarnessCollectorPlugin` 的 pytest hook 行为和 JSONL 输出

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不创建 `tests/test_runner.py`（proposal 建议的文件名与已有 `test_harness_runner.py` 冲突，会导致同模块两个测试文件）
- 不重复覆盖已有测试（事件 dataclass 4 个、HarnessResult 2 个、discover 3 个、run 的基本 pass/fail/error 8 个）
- 不修改其他源文件或测试文件

### 依赖的外部条件
- `pytest` 可用（项目已有 100+ 测试文件，基础设施完善）
- `zsiga/harness/runner.py` 当前代码不发生变更
- `tests/conftest_zsiga.py` 提供的 fixture 支持

## 目标

### 成功标准
1. `tests/test_harness_runner.py` 中新增 ≥ 3 个 `def test_` 函数，覆盖 `run_pytest()`、`_HarnessCollectorPlugin`、`TestReport`/`QualificationReport`
2. 新增测试不与现有 15 个测试功能重叠
3. `python -m pytest tests/test_harness_runner.py` 退出码 0，全部测试通过
4. 新增测试使用 `tmp_path`、monkeypatch 等标准 fixture，无外部环境依赖

### 验收方式
- `python -m pytest tests/test_harness_runner.py -v` 全绿
- `python -m ruff check tests/test_harness_runner.py` 无 lint 错误
- grep 验证新增 test_ 函数数 ≥ 3
- 人工审查：新增测试覆盖了 `run_pytest`、`_HarnessCollectorPlugin`、`TestReport`/`QualificationReport` 中的至少两个

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py` — 只读取分析，不修改
- `tests/test_harness_runner.py` 中**已有的测试类和函数**不得删除或修改签名（只追加）

### 项目部署分支
premium

### 已知风险
- **proposal 核心前提错误**：声称模块"缺少测试文件"，但 `test_harness_runner.py` 已存在。执行者可能误创建 `test_runner.py`（错误文件名）导致重复。必须在实现时确认扩展已有文件而非新建。
- **`run_pytest()` 调用 `pytest.main()`**：需注意测试中的 `pytest.main()` 可能与当前 pytest 会话交互，建议使用 `subprocess` 或 `pytest.main` + `--co` dry-run 模式隔离。
- **`_HarnessCollectorPlugin` 是私有类**（下划线前缀），测试时需通过 `from zsiga.harness.runner import _HarnessCollectorPlugin` 导入，可能触发 lint 警告（可接受）。
- **auto-generated proposal 历史风险**：同名 `add-tests-runner` 提案已出现 12+ 次，全部被 skip/reject，存在循环空转风险。

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类 auto-generated proposal 均被否决未执行，无 token 消耗基线）
