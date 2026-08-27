# clarify.md — add-tests-runner

> 需求工程师审查结论：**此 proposal 存在致命前提错误，建议驳回或大幅修订后重新提交。**

---

## 需求拆解

### 原始需求

Proposal 要求为模块 `zsiga/harness/runner.py`（317 行）创建测试文件 `tests/test_runner.py`，
声称该模块"缺少测试文件"，是潜在风险点。

### ⚠️ 事实核查结果

**核心前提不成立。** 目标模块已有测试文件：

| 已有文件 | 行数 | 覆盖范围 |
|---------|------|---------|
| `tests/test_harness_runner.py` | 227 行 | 事件 dataclass（TestEvent/TestStarted/TestPassed/TestFailed/TestError）、HarnessResult 聚合、HarnessRunner.discover() 发现逻辑、HarnessRunner.run() 的 pass/fail/error 分支 |

此外，proposal 的静态分析数据存在严重错误：

| 声称 | 实际 |
|------|------|
| 函数数: 0 | HarnessRunner 含 `__init__`、`discover`、`run`、`run_pytest`、`_run_file`、`_append_jsonl` 等方法 |
| "(无法提取函数列表)" | 模块有完整的方法定义 |
| BAC-02: `test_(待分析)` | 占位符，非合法测试函数名 |
| BAC-03: "至少 0 个 def test_" | 数学恒真，空文件即可满足 |

### 拆解后的子任务

> 以下任务基于 proposal 原始描述拆解，但受限于前提错误，实际执行价值存疑。

- [ ] 1. 确认现有测试覆盖范围并识别真正缺口（预估复杂度：中, 预估 token：~2000 / 无历史参考）
  - 文件范围：`tests/test_harness_runner.py`（读取分析）
  - 对比 `zsiga/harness/runner.py` 的公开 API，列出未被覆盖的函数/方法/类
  - 决定是扩展 `test_harness_runner.py` 还是新建文件

- [ ] 2. 为未覆盖的类和函数编写测试用例（预估复杂度：中, 预估 token：~3000 / 无历史参考）
  - 文件范围：`tests/test_harness_runner.py`（扩展）或新建 `tests/test_runner.py`
  - 候选目标：`_HarnessCollectorPlugin`（pytest hook 实现）、`HarnessRunner._run_file`（子进程隔离）、`HarnessRunner._append_jsonl`（JSONL 写入）
  - 使用 `unittest.mock` 隔离 subprocess/文件 I/O 依赖

- [ ] 3. 验证测试通过并满足修订后的验收标准（预估复杂度：低, 预估 token：~1000 / 无历史参考）
  - 文件范围：`tests/test_runner.py` 或扩展后的 `tests/test_harness_runner.py`
  - 运行 `python -m pytest` 确认退出码 0

---

## 边界

### IN scope
- 为 `zsiga/harness/runner.py` 中尚未被 `tests/test_harness_runner.py` 覆盖的公开/内部方法编写测试
- 使用 mock 隔离外部依赖（subprocess、文件 I/O）

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有的 `tests/test_harness_runner.py`（除非决定扩展而非新建）
- 不修改 `tests/conftest_zsiga.py`

### 依赖的外部条件
- `zsiga/harness/runner.py` 的 API 在实现期间保持稳定
- `tests/conftest_zsiga.py` 中的 fixture 可用
- 项目 pytest 基础设施正常工作（`python -m pytest` 可执行）

---

## 目标

### 成功标准

1. `zsiga/harness/runner.py` 的测试覆盖范围相比现有 `tests/test_harness_runner.py` 有**实质性增量**（新增 ≥3 个测试函数，覆盖此前未测的函数/方法/分支）
2. 所有新增测试可独立运行，不依赖运行时环境（LLM 服务、文件系统状态）
3. `python -m pytest tests/test_runner.py` 或扩展后的测试文件退出码 0
4. 新增测试通过 ruff lint 检查

### 验收方式

- **BAC-01（修订）**：测试文件存在且文件名合理（`tests/test_runner.py` 或扩展后的 `tests/test_harness_runner.py`）
- **BAC-02（修订）**：文件中存在 ≥3 个具有语义化命名的 `def test_` 函数（如 `test_harness_collector_plugin_collects_items`、`test_run_file_returns_harness_result` 等，**排除**占位符 `test_(待分析)`）
- **BAC-03（修订）**：`python -m pytest <测试文件>` 退出码 0
- **BAC-04（新增）**：新增测试覆盖的函数/方法在 `tests/test_harness_runner.py` 中**未被覆盖**（非重复测试）

> ⚠️ 原始 BAC-02（`test_(待分析)`）和 BAC-03（"至少 0 个 def test_"）已被替换，原版视为无效。

---

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- `zsiga/` 目录下所有源码文件

### 项目部署分支
- 未在 proposal 中指定（默认为当前工作分支）

### 已知风险

1. **重复测试风险（高）**：`tests/test_harness_runner.py` 已有 227 行测试覆盖 runner.py 的主要公开 API。如果不先分析已有覆盖范围，新建 `tests/test_runner.py` 极大概率产生大量重复测试。
2. **静态分析数据不可信（高）**：proposal 声称"函数数: 0"、"无法提取函数列表"，实际模块有完整的类方法定义。任何基于此数据的执行计划都需要重新分析源码。
3. **BAC 形同虚设（高）**：原始 BAC-02 是占位符，BAC-03 要求"至少 0 个"测试函数。未修订前，一个空文件即可通过全部验收标准。
4. **文件命名冲突（中）**：创建 `tests/test_runner.py` 与已有的 `tests/test_harness_runner.py` 并存，可能导致混淆。建议统一扩展已有文件或使用更明确的命名。
5. **自演进引擎产物（中）**：此 proposal 由 zsiga 自演进引擎自动生成，未经人工审查，静态分析存在系统性盲区（只按文件名匹配 `test_runner.py`，忽略了实际存在的 `test_harness_runner.py`）。

### 预估 token 消耗
- prompt: ~4000（含源码阅读、已有测试分析）
- completion: ~2500（测试代码生成）
- 数据来源: 无历史参考（同类 auto-generated 测试 proposal 均被驳回）
