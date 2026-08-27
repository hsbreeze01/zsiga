# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 函数）添加单元测试文件 `tests/test_duration_predictor.py`。

**关键事实校正**：proposal 声称"模块缺少测试文件"，但实际上 `tests/test_phase_duration.py`（241 行）已包含 9 个直接测试该模块的用例，覆盖 `_fit_linear` 和 `predict_change_duration` 的核心路径。真正的缺口是 `_collect_known_phases` 和 `_fallback_estimates` 两个私有函数缺少**直接测试**（目前仅被间接调用覆盖）。

### 拆解后的子任务
- [ ] 1. 为 `_collect_known_phases` 和 `_fallback_estimates` 编写直接单元测试，放入**已有文件** `tests/test_phase_duration.py` 中，补齐覆盖缺口 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 2. 若 proposal BAC 要求必须创建 `tests/test_duration_predictor.py`，则创建该文件并导入已有测试或编写补充测试，确保 BAC-01~04 全部通过 (预估复杂度：低, 预估 token：~1000 / 无历史参考)

## 边界

### IN scope
- 为 `_collect_known_phases(phase_stats)` 添加直接测试（提取已知 phase 名称集合）
- 为 `_fallback_estimates(phase_stats)` 添加直接测试（基于历史数据生成 fallback 估算）
- 确保 `tests/test_duration_predictor.py` 文件存在且通过 pytest（满足 BAC）
- 测试可独立运行，不依赖运行时环境

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不重复覆盖 `_fit_linear`、`_predict_phase`、`predict_change_duration` 已有测试的逻辑（`tests/test_phase_duration.py` 已有 9 个用例）
- 不修改已有测试文件中的现有测试

### 依赖的外部条件
- `zsiga/duration_predictor.py` 中的 5 个函数签名保持不变
- `tests/test_phase_duration.py` 已有测试继续通过
- 项目 Python 环境（3.10+）和 pytest 可用

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在（BAC-01）
2. 该文件包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个具名测试函数（BAC-02）
3. 该文件包含至少 3 个 `def test_` 函数（BAC-03）
4. `python -m pytest tests/test_duration_predictor.py` 退出码 0（BAC-04）
5. 已有测试不受影响：`python -m pytest tests/test_phase_duration.py` 退出码 0

### 验收方式
- `test -f tests/test_duration_predictor.py` 验证文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 验证测试数量 ≥ 3
- `python -m pytest tests/test_duration_predictor.py -v` 验证全部通过
- `python -m pytest tests/test_phase_duration.py -v` 验证回归无影响

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析）
- `tests/test_phase_duration.py` 中的已有测试（可追加新测试但不改动已有内容）

### 项目部署分支
- deploy

### 已知风险
- **僵尸提案循环**：此 proposal 已被生成 13+ 轮并全部 skipped/rejected，根因是提案引擎只检查精确文件名 `test_duration_predictor.py` 是否存在，未识别 `test_phase_duration.py` 中已有覆盖。若本次执行成功创建文件，后续引擎应不再重复生成
- **冗余覆盖风险**：BAC-02 要求的 `test__fit_linear` 和 `test__predict_phase` 已在 `test_phase_duration.py` 中有充分覆盖，新文件中的测试应避免简单重复，可侧重不同边界条件或更细粒度的断言
- **已有测试回归**：新文件中的 import 或 fixture 不得干扰已有测试文件的运行

### 预估 token 消耗
- prompt: ~2000
- completion: ~1500
- 数据来源: 无历史参考（此 proposal 此前从未成功执行）
