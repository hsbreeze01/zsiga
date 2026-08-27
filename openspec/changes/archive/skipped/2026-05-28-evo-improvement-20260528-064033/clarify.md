# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 函数）添加单元测试文件 `tests/test_duration_predictor.py`。

### ⚠️ 关键事实纠正
proposal 声称该模块"缺少测试文件"——**前提不完全成立**。`tests/test_phase_duration.py`（241 行）已包含以下覆盖：
- `TestFitLinear` — 直接测试 `_fit_linear`（已知系数恢复、空输入）
- `TestPredictChangeDurationSufficient` / `Insufficient` — 通过公开 API 测试
- `TestNegativeClamping` / `TestMissingPhaseKeys` — 边界场景

**真正缺口**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数仅有间接覆盖，缺乏独立直接测试。

### 拆解后的子任务
- [ ] 1. 为 `_collect_known_phases` 编写独立单元测试（预估复杂度：低, 预估 token：~1500）
  - 测试正常 phase_stats 字典输入 → 返回已知阶段列表
  - 测试空输入 / 无有效键输入 → 返回空列表
- [ ] 2. 为 `_predict_phase` 编写独立单元测试（预估复杂度：中, 预估 token：~2500）
  - 测试 records ≥ 3 条时走线性预测路径
  - 测试 records < 3 条时走 fallback 路径
  - 测试 project_lines / proposal_chars 参数对预测值的缩放影响
- [ ] 3. 为 `_fallback_estimates` 编写独立单元测试（预估复杂度：低, 预估 token：~1500）
  - 测试正常 phase_stats 输入 → 返回含 total 的估算字典
  - 测试空 / 缺失键输入 → 合理降级行为
- [ ] 4. 创建 `tests/test_duration_predictor.py` 并整合全部测试（预估复杂度：低, 预估 token：~500）
  - 确保 import 路径正确、文件结构符合项目惯例
  - 确认 `python -m pytest tests/test_duration_predictor.py` 退出码 0

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的直接独立测试
- 满足 BAC-01~04：文件存在、目标函数有对应 test、≥ 3 个 `def test_`、pytest 通过
- 可补充 `_fit_linear` 的额外边界场景（不与 `test_phase_duration.py` 重复）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改 `tests/test_phase_duration.py`（现有测试保持不动）
- 不引入新依赖
- 不做集成测试或端到端测试

### 依赖的外部条件
- `zsiga/duration_predictor.py` 中的 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 可被直接 import（以 `_` 前缀的私有函数需确认 import 可达性）
- pytest 运行环境正常（`conftest_zsiga.py` 提供 sys.path 设置）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 ≥ 3 个 `def test_` 函数
2. 文件中存在直接测试 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的测试函数
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. 新测试与 `tests/test_phase_duration.py` 无实质性重复

### 验收方式
- BAC-01: `test -f tests/test_duration_predictor.py`
- BAC-02: `grep -c 'def test__collect_known_phases\|def test__predict_phase\|def test__fallback_estimates' tests/test_duration_predictor.py` ≥ 3（或函数名变体，核心是覆盖这三个目标）
- BAC-03: `grep -c 'def test_' tests/test_duration_predictor.py` ≥ 3
- BAC-04: `python -m pytest tests/test_duration_predictor.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（只读分析）
- `tests/test_phase_duration.py`（已有测试，不触碰）

### 项目部署分支
- main

### 已知风险
- 私有函数（`_` 前缀）的 import 可达性：需通过 `from zsiga.duration_predictor import _collect_known_phases` 等方式导入，确认项目无 lint 规则禁止此类导入
- 与 `test_phase_duration.py` 的测试内容重叠风险：需避免复制已有测试场景，聚焦于三个未直接覆盖的私有函数
- proposal 已被 steward 多次驳回（5+ 次），核心争议为"已有覆盖 vs 新建文件"。本次 clarify 明确了真正的测试缺口，降低重复风险

### 预估 token 消耗
- prompt: ~3000
- completion: ~2500
- 数据来源: 无历史参考（同类 auto-generated proposal 多被驳回，无成功执行记录可参照）
