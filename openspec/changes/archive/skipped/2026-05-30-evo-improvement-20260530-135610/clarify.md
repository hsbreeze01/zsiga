# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
模块 `zsiga/duration_predictor.py`（164 行，5 函数，0 类，0 lint 问题，无高 CC 函数）缺少对应的测试文件 `tests/test_duration_predictor.py`。需要为该模块的全部公开函数编写单元测试，确保核心预测逻辑的回归安全。

### 拆解后的子任务

- [ ] 1. **覆盖数据收集与回退估算函数**：为 `_collect_known_phases(phase_stats)` 和 `_fallback_estimates(phase_stats)` 编写测试，验证正常输入、空输入、边界情况的返回结构 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 2. **覆盖线性拟合函数**：为 `_fit_linear(xs1, xs2, ys)` 编写测试，覆盖正常拟合、退化输入（单点/共线/空数据）、返回值格式 (预估复杂度：中, 预估 token：~2500 / 无历史参考)
- [ ] 3. **覆盖单阶段预测与总入口函数**：为 `_predict_phase(records, phase_name, project_lines, proposal_chars)` 和 `predict_change_duration(phase_stats, project_lines, proposal_chars)` 编写测试，验证完整预测流程、回退路径、返回字典结构 (预估复杂度：中, 预估 token：~2500 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 覆盖全部 5 个函数：`_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration`
- 测试通过 `python -m pytest tests/test_duration_predictor.py` 退出码 0
- 测试通过 `ruff check tests/test_duration_predictor.py` 无报错

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改其他已有测试文件或源码文件
- 不修改 `zsiga.yaml`、`pyproject.toml`、`requirements.txt`

### 依赖的外部条件
- `zsiga/duration_predictor.py` 存在且可正常 import
- `pytest` 和 `ruff` 可用
- 无需外部 LLM 服务或文件系统特殊状态（模块为纯数学/数据计算，无 I/O 依赖）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 存在且包含至少 5 个 `def test_` 函数（覆盖全部 5 个函数）
2. BAC-02 指定的 3 个函数名测试存在：`test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0，全部测试通过
4. `ruff check tests/test_duration_predictor.py` 无报错

### 验收方式
- 检查文件是否存在：`test -f tests/test_duration_predictor.py`
- 检查函数名：`grep -c 'def test_' tests/test_duration_predictor.py` ≥ 5
- 运行 pytest：`python -m pytest tests/test_duration_predictor.py -v`
- 运行 ruff：`ruff check tests/test_duration_predictor.py`

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`
- 所有已有 `tests/test_*.py` 文件
- `zsiga.yaml`、`pyproject.toml`、`requirements.txt`

### 项目部署分支
- deploy

### 已知风险
- `_fit_linear` 是模块中最复杂的函数（54 行），包含 numpy 风格的线性拟合逻辑，需要仔细构造测试数据验证回归正确性
- 模块函数名以下划线开头（如 `_collect_known_phases`），属内部函数但仍需覆盖，测试中直接 import 即可

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（`duration_predictor` 为首次测试提案，无 archive 记录）
