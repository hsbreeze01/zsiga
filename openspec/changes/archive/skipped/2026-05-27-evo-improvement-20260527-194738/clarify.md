# Clarify: add-tests-duration_predictor

## 需求拆解

### 原始需求
为无测试模块 `zsiga/duration_predictor.py`（164 行, 5 个函数, 0 个类）创建单元测试文件 `tests/test_duration_predictor.py`，覆盖所有函数的核心路径。模块为纯计算逻辑（线性回归 + 中位数兜底），无外部依赖需 mock。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_duration_predictor.py` 骨架并测试 `_collect_known_phases`（预估复杂度：低, 预估 token：~1500）
  - 测试正常多记录提取唯一阶段名
  - 测试空列表输入
  - 测试单条记录
  - 测试阶段名去重

- [ ] 2. 测试 `_fit_linear` 及其退化路径（预估复杂度：中, 预估 token：~2500）
  - 正常 2 特征线性回归（已知系数恢复）
  - 空输入
  - 退化矩阵路径 `abs(D) < 1e-12`（如 xs1 == xs2 完全共线性）
  - 单样本输入

- [ ] 3. 测试 `_predict_phase` 独立函数（预估复杂度：中, 预估 token：~2000）
  - ≥3 条记录走回归路径
  - <3 条记录走中位数兜底
  - 预测值负值钳位为 0
  - 空记录输入

- [ ] 4. 测试 `_fallback_estimates` 和主入口 `predict_change_duration`（预估复杂度：中, 预估 token：~2000）
  - `_fallback_estimates`: 正常中位数计算、空输入、单阶段
  - `predict_change_duration`: ≥3 条记录完整回归、<3 条兜底、空输入返回空 dict、返回值含 `_total` 键

- [ ] 5. 全量 pytest 验证与 BAC 达标检查（预估复杂度：低, 预估 token：~500）
  - `python -m pytest tests/test_duration_predictor.py` 退出码 0
  - 确认 ≥3 个 `def test_` 函数存在
  - 确认 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个符号存在
  - 全项目 `python -m pytest` 无回归

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 覆盖 `_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration` 的核心路径
- 包含 BAC 要求的三个命名测试函数：`test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改 `tests/test_phase_duration.py`（已有的部分覆盖测试）
- 不修改 `zsiga/metrics/collector.py` 或其他模块
- 不涉及 pipeline/agent 自身代码

### 依赖的外部条件
- `zsiga/duration_predictor.py` 可正常 import（纯 Python，无外部依赖）
- `tests/test_phase_duration.py` 已有部分覆盖，新测试不应与之冲突
- 项目使用 pytest 作为测试框架

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 三个 BAC 指定符号存在：`test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. 全项目 `python -m pytest` 无回归（无新增失败）

### 验收方式
- `grep -c "def test_" tests/test_duration_predictor.py` 计数 ≥ 3
- `python -c "import ast; ..."` 或 `grep "def test__collect_known_phases\|def test__fit_linear\|def test__predict_phase" tests/test_duration_predictor.py` 确认三个符号
- `python -m pytest tests/test_duration_predictor.py -v` 退出码 0
- `python -m pytest` 退出码 0（全量回归检查）

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析）
- `tests/test_phase_duration.py`（已有测试，不动）
- 任何非测试源码文件

### 项目部署分支
- main

### 已知风险
- 与已有 `tests/test_phase_duration.py` 的覆盖可能存在重叠（该文件已覆盖 `_fit_linear` 和 `predict_change_duration`），新测试应聚焦未覆盖路径，避免重复测试导致维护负担
- `_fit_linear` 实现了手写最小二乘法（含克莱姆法则求解），退化矩阵路径需构造特定输入才能触发
- 模块所有函数均为纯计算，无需 mock 外部依赖

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考（基于函数复杂度和测试场景数量估算）
