# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数，纯计算模块）新建独立测试文件 `tests/test_duration_predictor.py`，覆盖现有 `tests/test_phase_duration.py` 未直接测试的 3 个私有函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`），以及 `_fit_linear` 的退化场景。

### 拆解后的子任务

- [ ] 1. **创建测试文件骨架 + `_collect_known_phases` 直接测试** (预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 新建 `tests/test_duration_predictor.py`
  - 导入 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates`、`_fit_linear`、`predict_change_duration`
  - 编写 `test__collect_known_phases` 覆盖：空列表、缺失 `phases` key、重复阶段名去重、正常多阶段提取

- [ ] 2. **`_predict_phase` + `_fallback_estimates` 直接测试** (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 编写 `test__predict_phase` 覆盖：≥3 样本回归路径、<3 样本中位数回退、0 样本 `DEFAULT_PHASE_SECONDS` 回退、负值钳位
  - 编写 `test__fallback_estimates` 覆盖：空输入、单条记录、排序 key 正确性、`_total` 汇总值
  - 补充 `_fit_linear` 退化场景（共线输入、全相同值）

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含至少 3 个 `def test_` 函数
- 直接测试 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数
- 补充 `_fit_linear` 退化场景（与现有 `TestFitLinear` 不重复）
- BAC 要求的 3 个具名测试函数：`test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改现有 `tests/test_phase_duration.py`
- 不重复已有测试覆盖（`predict_change_duration` 主路径已在 `test_phase_duration.py` 中测试）
- 不引入 mock（模块为纯计算，无外部依赖）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 中 `_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates` 可被直接导入（当前均为模块级函数，无 `__all__` 限制）
- `pytest` 可在项目环境中正常运行
- 现有 `tests/test_phase_duration.py` 测试不被新测试文件破坏

## 目标

### 成功标准
1. 文件 `tests/test_duration_predictor.py` 存在且包含 BAC 要求的 3 个具名测试函数
2. `python -m pytest tests/test_duration_predictor.py` 退出码 0
3. `python -m pytest tests/test_phase_duration.py` 退出码仍为 0（无回归）
4. 新测试直接覆盖 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates`，与已有 `test_phase_duration.py` 形成互补而非重复

### 验收方式
- `test -f tests/test_duration_predictor.py` 确认文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 确认 ≥3
- `grep 'test__collect_known_phases\|test__fit_linear\|test__predict_phase' tests/test_duration_predictor.py` 确认 BAC-02 具名函数存在
- `python -m pytest tests/test_duration_predictor.py -v` 退出码 0
- `python -m pytest tests/test_phase_duration.py -v` 退出码 0（回归检查）

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`
- `tests/test_phase_duration.py`
- `pyproject.toml`、`requirements.txt`（不新增依赖）

### 项目部署分支
- deploy

### 已知风险
- **已有测试文件共存**：`tests/test_phase_duration.py` 已覆盖 `_fit_linear` 正常路径和 `predict_change_duration` 主路径，新文件需避免重复断言相同场景
- **僵尸循环历史**：`add-tests-duration_predictor` proposal 在 archive 中有 13+ 轮 skipped 记录，需确保本次交付可实际通过 pytest 而非再次被 archive
- **私有函数导入**：`_collect_known_phases` 等带下划线前缀函数虽可导入，但属于内部实现细节，未来版本可能变更签名

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（纯计算模块测试，预估基于函数数量和复杂度）
