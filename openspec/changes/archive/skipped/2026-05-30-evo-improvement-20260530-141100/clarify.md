# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行, 5 函数）添加专属单元测试文件 `tests/test_duration_predictor.py`，补全现有 `tests/test_phase_duration.py` 中缺失的直接覆盖。

**事实修正**：proposal 声称"缺少测试文件"，但 `tests/test_phase_duration.py`（241 行, 9 个测试类, 14+ 个 `def test_`）已通过公开 API `predict_change_duration` 间接覆盖了所有 5 个函数。其中 `_fit_linear` 已有 `TestFitLinear` 直接测试（2 个 case）。真正缺失的是 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数的**独立直接测试**，以及 `_fit_linear` 的退化/边界情况。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_duration_predictor.py`，编写 `_collect_known_phases` 和 `_fallback_estimates` 的直接单元测试（预估复杂度：低, 预估 token：~2000）
  - `_collect_known_phases`：正常多 phase 提取、空列表输入、单条记录、重复 phase 去重
  - `_fallback_estimates`：正常中位数回退、空列表、单阶段、多阶段混合
- [ ] 2. 编写 `_predict_phase` 的直接单元测试（预估复杂度：中, 预估 token：~2500）
  - 足够记录（≥3）时的线性预测 + ≥0 钳位
  - 不足记录时的 None 返回
  - `project_lines` / `proposal_chars` 系数影响
- [ ] 3. 补充 `_fit_linear` 退化/边界情况测试（预估复杂度：中, 预估 token：~2000）
  - 共线输入（行列式≈0）行为验证
  - 全零输入、单点输入
  - 大数值范围稳定性
  - 注：基础正确性已由 `test_phase_duration.py::TestFitLinear` 覆盖，此处只补边界

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 为 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 编写独立直接测试
- 为 `_fit_linear` 补充退化/边界测试
- 满足 BAC-01 ~ BAC-04 验收条件

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有 `tests/test_phase_duration.py`
- 不重复 `test_phase_duration.py` 已覆盖的场景（如 `_fit_linear` 基础正确性、`predict_change_duration` 正常/不足记录路径、负值钳位）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 的 5 个函数签名不变（当前为纯函数，无外部依赖，无 LLM/IO 调用）
- 现有 `tests/test_phase_duration.py` 通过（作为回归基线）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个具名函数（BAC-01, BAC-02）
2. 文件中至少 3 个 `def test_` 函数（BAC-03）
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0（BAC-04）
4. 新测试与 `tests/test_phase_duration.py` 不产生功能重复——新测试聚焦私有函数直接覆盖和边界情况

### 验收方式
- `test -f tests/test_duration_predictor.py`（BAC-01）
- `grep -c 'def test_' tests/test_duration_predictor.py` ≥ 3（BAC-03）
- `python -m pytest tests/test_duration_predictor.py -v` 全部 PASSED（BAC-04）
- `python -m pytest tests/test_phase_duration.py` 仍全部 PASSED（回归验证）

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析）
- `tests/test_phase_duration.py`（已有覆盖，不动）

### 项目部署分支
- deploy（主开发分支）

### 已知风险
- **僵尸循环风险**：此 proposal 已迭代 20+ 轮均未落地（archive/skipped），属于引擎 basename 匹配缺陷导致的循环生成。需确保本轮执行产出的测试文件**不与 `test_phase_duration.py` 重复**，避免被后续 gate 审查以"冗余"为由 reject
- **已有覆盖重叠**：`test_phase_duration.py` 已间接覆盖全部函数，新测试必须聚焦增量价值（直接调用私有函数、边界/退化 case），否则无实质意义
- **纯函数测试**：目标模块所有函数均为纯函数（无 IO、无 LLM 调用），无需 mock 隔离，测试应直接构造输入断言输出

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（此前 20+ 轮均未执行到 implementation 阶段）
