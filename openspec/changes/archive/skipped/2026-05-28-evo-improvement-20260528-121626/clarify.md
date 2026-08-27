# clarify.md — add-tests-runner

> **⚠️ 需求工程师标注：此 proposal 建立在错误前提上。**
> `tests/test_harness_runner.py`（227 行）已存在，覆盖了 `zsiga/harness/runner.py` 的核心公开接口。
> BAC 中 "至少 0 个 test_ 函数" 和 "test_(待分析)" 占位符使验收标准形同虚设。
> 以下按 proposal 原始需求拆解，但标注了每一项的实际状态。

---

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（317 行，10 个类）添加单元测试文件 `tests/test_runner.py`，覆盖公开函数。

**实际情况：**
- `tests/test_harness_runner.py` 已存在，包含 4 个测试类、16+ 个 `def test_` 函数
- 覆盖范围：TestEvent 系列 dataclass（5 个）、HarnessResult 聚合、HarnessRunner.discover()（3 场景）、HarnessRunner.run()（8 场景含 pass/fail/error）
- proposal 要求的文件名 `test_runner.py` 与已有文件 `test_harness_runner.py` 不一致，会导致同模块出现两个测试文件

### 拆解后的子任务

- [ ] 1. **确认现有测试覆盖缺口** — 对比 `tests/test_harness_runner.py` 已有覆盖与 `zsiga/harness/runner.py` 全部公开 API，定位真正未测试的类/方法（预估复杂度：低，预估 token：~1500 / 无历史参考）
  - runner.py 实际包含：`HarnessRunner`（`discover`, `run`, `run_pytest`, `_run_file`, `_append_jsonl`）、`_HarnessCollectorPlugin`（pytest hooks）、5 个 Event dataclass、`HarnessResult`、`TestReport`、`QualificationReport`
  - 已有测试文件覆盖：Event dataclass 默认值、HarnessResult、discover 三场景、run 八场景
  - 可能未覆盖：`_HarnessCollectorPlugin` 的 pytest hook 方法、`run_pytest` 独立调用、`TestReport`/`QualificationReport` dataclass、`_append_jsonl` 私有方法

- [ ] 2. **为确认的覆盖缺口编写测试** — 在已有 `test_harness_runner.py` 中补充缺失测试，或在新建文件中按需添加（预估复杂度：低，预估 token：~2000 / 无历史参考）
  - 注意：proposal 要求新建 `tests/test_runner.py`，但已有 `tests/test_harness_runner.py`——应优先扩展已有文件而非创建同名异构文件
  - 如确实新建 `tests/test_runner.py`，需避免与已有测试重复

- [ ] 3. **验证全部测试通过** — `python -m pytest tests/test_runner.py tests/test_harness_runner.py` 退出码 0（预估复杂度：低，预估 token：~500 / 无历史参考）

---

## 边界

### IN scope
- 为 `zsiga/harness/runner.py` 中尚未被 `tests/test_harness_runner.py` 覆盖的公开 API 编写测试
- 测试必须可独立运行，不依赖运行时 LLM 调用或外部服务

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有的 `tests/test_harness_runner.py`（除非决定扩展而非新建）
- 不覆盖私有方法（`_run_file`, `_append_jsonl` 等）——除非是补全关键路径
- 不涉及其他模块的测试

### 依赖的外部条件
- `zsiga/harness/runner.py` 源码结构稳定，近期无重构计划
- `tests/conftest_zsiga.py` 提供必要的 pytest fixture
- pytest 基础设施正常运行

---

## 目标

### 成功标准
1. `zsiga/harness/runner.py` 的所有公开类和主要方法有直接测试覆盖（不依赖间接调用）
2. 新增测试与已有 `tests/test_harness_runner.py` 不重复
3. 全部测试通过（`pytest` 退出码 0）
4. 新增测试文件经 `ruff check` 无 lint 错误

### 验收方式
- **手动审查**：逐函数对比已有测试 vs 新增测试，确认无冗余
- **自动化**：`python -m pytest tests/test_runner.py -v` 退出码 0
- **注意**：proposal 原始 BAC（BAC-02 占位符、BAC-03 "至少 0 个"）不可作为有效验收标准，需按上述标准执行

---

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- `tests/test_harness_runner.py`（除非明确决定扩展而非新建）
- `tests/conftest_zsiga.py`

### 项目部署分支
- 未指定（proposal 未提及，遵循项目默认分支策略）

### 已知风险
1. **核心前提错误（高风险）**：proposal 声称 runner.py "缺少测试文件"，但 `tests/test_harness_runner.py` 已有 227 行、16+ 测试函数。执行前必须先做覆盖缺口分析，否则大概率产出重复测试
2. **文件命名冲突（中风险）**：新建 `tests/test_runner.py` 会导致 `runner.py` 对应两个测试文件（`test_runner.py` + `test_harness_runner.py`），增加维护混乱
3. **BAC 失效（高风险）**：原始 BAC-02 是占位符 `test_(待分析)`，BAC-03 要求 "至少 0 个 test_ 函数"。空文件即可通过全部原始 BAC，不能作为质量门控
4. **静态分析数据不可信（中风险）**：proposal 声称 "函数数: 0"、"无法提取函数列表"，但 HarnessRunner 有 `discover()`、`run()`、`run_pytest()`、`_run_file()` 等方法。所有分析需重新做

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（同类 proposal 均在 gate 阶段被 reject/pushback，无执行记录）
