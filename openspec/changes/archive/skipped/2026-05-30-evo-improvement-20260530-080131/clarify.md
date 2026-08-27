# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数）创建独立测试文件 `tests/test_duration_predictor.py`，覆盖全部 5 个函数的单元测试。Proposal 声称该模块缺少测试文件。

**⚠️ 关键事实校验**：并行探索已确认 `tests/test_phase_duration.py`（241 行，9 个测试方法）已直接导入并测试了 `_fit_linear` 和 `predict_change_duration`。仅有 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase` 三个内部函数缺乏独立单元测试（目前通过 `predict_change_duration` 间接覆盖）。此 proposal 的"缺少测试文件"前提部分不成立——测试已存在但以不同文件名组织。

### 拆解后的子任务

- [ ] 1. **创建 `tests/test_duration_predictor.py` 测试文件骨架并实现全部 5 个函数的单元测试** (预估复杂度：中, 预估 token：~6000 / 无历史参考)
  - 文件范围：`tests/test_duration_predictor.py`（新建）
  - 覆盖目标：`_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration`
  - 必须包含 BAC-02 指定的 3 个测试函数：`test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`
  - 补充 `test__fallback_estimates` 和 `test_predict_change_duration` 以覆盖全部 5 函数
  - 使用 mock 隔离外部依赖，确保测试可独立运行
  - **注意**：与已有 `tests/test_phase_duration.py` 存在覆盖重叠（`_fit_linear`、`predict_change_duration` 已有直接测试），新增测试应侧重补充边界场景而非重复已有断言

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含至少 3 个 `def test_` 函数（BAC-03）
- 覆盖 `_collect_known_phases`、`_fit_linear`、`_predict_phase`（BAC-02 硬性要求）
- 补充 `_fallback_estimates`、`predict_change_duration` 测试以完整覆盖全部 5 函数
- 确保 `python -m pytest tests/test_duration_predictor.py` 退出码 0（BAC-04）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有的 `tests/test_phase_duration.py`
- 不修改 `conftest` 或其他测试基础设施

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块可正常导入（当前 ruff lint 0 问题，无已知导入错误）
- 已有测试文件 `tests/test_phase_duration.py` 不产生命名冲突或 fixture 冲突
- **风险提示**：此 proposal 已被自演进引擎生成 26+ 次并全部被 skip/archive/pushback，历史成功率 0%。核心异议是"已有测试覆盖"和"重复劳动"。执行前应确认是否确实需要新文件，还是应将增量测试追加到现有 `test_phase_duration.py`

## 目标

### 成功标准
1. 文件 `tests/test_duration_predictor.py` 存在于 `tests/` 目录
2. 该文件包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个测试函数（BAC-02）
3. 该文件包含至少 3 个 `def test_` 函数（BAC-03）
4. `python -m pytest tests/test_duration_predictor.py` 退出码为 0（BAC-04）
5. 测试与已有 `tests/test_phase_duration.py` 共存不冲突

### 验收方式
- `ls tests/test_duration_predictor.py` 确认文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 确认测试函数数量 ≥ 3
- `grep 'test__collect_known_phases\|test__fit_linear\|test__predict_phase' tests/test_duration_predictor.py` 确认 BAC-02 函数存在
- `python -m pytest tests/test_duration_predictor.py -v` 退出码 0
- `python -m pytest tests/` 确认全量测试不回归

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析）
- `tests/test_phase_duration.py`（已有测试，不碰）
- `tests/conftest_zsiga.py`（共享 conftest）
- 所有 `zsiga/` 源码文件

### 项目部署分支
deploy

### 已知风险
- **重复覆盖风险**：`tests/test_phase_duration.py` 已直接测试 `_fit_linear`（2 个测试方法）和 `predict_change_duration`（5 个测试方法），新建文件可能产生语义重复
- **历史循环风险**：此 proposal 已被生成 26+ 次，全部失败。引擎的静态分析用 `basename` 匹配测试文件名，无法发现 `test_phase_duration.py` 已覆盖 `duration_predictor.py`，导致持续误判"缺少测试"
- **增量价值有限**：仅 `_collect_known_phases` 和 `_fallback_estimates` 缺乏独立单元测试，可通过在现有文件追加 2-3 个测试解决，无需新建文件
- **全量测试回归**：新测试必须与已有 50+ 个测试文件共存，不能引入 fixture 冲突或导入错误

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（同类任务从未成功完成）
