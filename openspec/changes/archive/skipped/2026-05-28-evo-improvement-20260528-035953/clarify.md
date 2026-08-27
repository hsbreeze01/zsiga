# clarify.md — add-tests-duration_predictor

> **⚠️ 前置审查警告**：并行探索确认 `tests/test_phase_duration.py`（241 行，6 个测试类，~16 个 test 方法）已直接导入并测试 `zsiga/duration_predictor.py` 的 `_fit_linear` 和 `predict_change_duration`。Proposal 的核心前提"模块缺少测试文件"**不成立**。下方需求拆解基于"识别并填补真正覆盖缺口"重新梳理。

---

## 需求拆解

### 原始需求
Proposal 要求为 `zsiga/duration_predictor.py`（164 行，5 函数）新建 `tests/test_duration_predictor.py`，声称该模块缺少测试文件。BAC 要求文件存在、包含 `test__collect_known_phases` / `test__fit_linear` / `test__predict_phase`、至少 3 个 `def test_` 函数、pytest 退出码 0。

### 已有覆盖现状（探索确认）

| 函数 | 已有测试覆盖 | 来源 |
|---|---|---|
| `_collect_known_phases(phase_stats)` | ❌ 无直接测试 | — |
| `_fit_linear(xs1, xs2, ys)` | ✅ 已覆盖 | `TestFitLinear` in `test_phase_duration.py` |
| `_predict_phase(records, phase_name, ...)` | ❌ 无直接测试 | — |
| `_fallback_estimates(phase_stats)` | ❌ 无直接测试（仅通过 `predict_change_duration` 间接覆盖） | — |
| `predict_change_duration(phase_stats, ...)` | ✅ 已充分覆盖 | `TestPredictChangeDurationSufficient/Insufficient/NegativeClamping/MissingPhaseKeys` |

### 拆解后的子任务

- [ ] 1. **确认覆盖缺口并决定执行策略** (预估复杂度：低, 预估 token：~1500)
  - 核实 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 在 `test_phase_duration.py` 中是否已有任何直接或间接覆盖
  - 决定：是新建 `test_duration_predictor.py`（按 proposal BAC）还是扩展现有 `test_phase_duration.py`
  - **建议**：扩展现有文件避免重复，但 BAC-01 硬性要求新建 `test_duration_predictor.py`，需注意与 BAC 的兼容性

- [ ] 2. **为未覆盖的私有函数编写单元测试** (预估复杂度：低, 预估 token：~2000)
  - `_collect_known_phases(phase_stats)` — 测试：空输入返回空集、多阶段去重、单阶段输入
  - `_predict_phase(records, phase_name, ...)` — 测试：≥3 条记录走回归路径、<3 条走中位数回退、空记录处理、负值钳制
  - `_fallback_estimates(phase_stats)` — 测试：空输入、单阶段、多阶段、含 `_total` 求和一致性
  - **注意**：`_fit_linear` 已在 `TestFitLinear` 中覆盖，BAC-02 要求的 `test__fit_linear` 将产生重复测试

- [ ] 3. **验证测试通过并满足 BAC** (预估复杂度：低, 预估 token：~500)
  - `python -m pytest tests/test_duration_predictor.py` 退出码 0
  - `ruff check tests/test_duration_predictor.py` 无 lint 错误
  - 确认 BAC-01~04 全部满足

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`（满足 BAC-01）
- 为 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 编写直接单元测试
- 包含 `test__fit_linear` 以满足 BAC-02（即使与已有测试重复）
- 满足 BAC-03（≥3 个 `def test_` 函数）和 BAC-04（pytest 通过）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改 `tests/test_phase_duration.py`
- 不修改 pipeline、daemon、config 等其他模块
- 不重构现有测试文件（如合并/迁移）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 的内部函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）可被直接导入测试（模块无 `__all__` 限制）
- pytest 基础设施就绪（`conftest_zsiga.py` 存在）
- `test_phase_duration.py` 中已有的辅助函数（`_make_changes`、`_make_stats`）可参考其模式但不可直接导入（不同文件）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个函数名（BAC-02）
2. 文件中至少 3 个 `def test_` 函数（BAC-03）
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0（BAC-04）
4. 新测试为 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 提供此前缺失的直接覆盖

### 验收方式
- `test -f tests/test_duration_predictor.py`
- `grep -c 'def test_' tests/test_duration_predictor.py` ≥ 3
- `grep -q 'def test__collect_known_phases' tests/test_duration_predictor.py`
- `grep -q 'def test__fit_linear' tests/test_duration_predictor.py`
- `grep -q 'def test__predict_phase' tests/test_duration_predictor.py`
- `python -m pytest tests/test_duration_predictor.py` 退出码 0
- `ruff check tests/test_duration_predictor.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py` — 仅读取分析，不修改源码
- `tests/test_phase_duration.py` — 不修改已有测试
- `zsiga/daemon.py`、`zsiga/config.py` 等非目标模块

### 项目部署分支
- 变更目录：`openspec/changes/evo-improvement-20260528-035953`
- 目标项目根目录：`/home/zsiga/repo`

### 已知风险
- **重复测试风险（中等）**：BAC-02 要求 `test__fit_linear`，但 `TestFitLinear` 已在 `test_phase_duration.py` 中覆盖相同函数。执行后同一函数在两个文件中被测试，增加维护负担。proposal 被反复驳回（≥3 次 skipped + 多次 PUSHBACK）的核心原因即此
- **proposal 前提不成立（高）**：核心问题陈述"模块缺少测试文件"是事实性错误。`test_phase_duration.py` 已有充分覆盖。此 proposal 若执行，实质价值仅限于 3 个私有函数的直接测试
- **自演进引擎生成标记**：proposal 声明由 zsiga 自演进引擎生成，历史上有同类 proposal 被反复驳回的记录（`evolution.budget_cap_hit` 模式）
- **历史反复驳回**：至少 3 个同类 proposal 已被 skip（20260527-194738、20260528-013154、20260528-021723）， steward 多次以"已有覆盖"、"重复劳动"为由驳回

### 预估 token 消耗
- prompt: ~3000（读取源模块 + 已有测试 + 新文件上下文）
- completion: ~1500（生成约 100-150 行测试代码）
- 数据来源: 无历史参考（同类 proposal 从未通过执行阶段）
