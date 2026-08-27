# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 函数，0 类）创建单元测试文件 `tests/test_duration_predictor.py`。该模块当前无直接对应的测试文件（已有 `tests/test_phase_duration.py` 覆盖部分函数，但 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个函数完全未覆盖）。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_duration_predictor.py` 并编写 `_collect_known_phases` 测试组（预估复杂度：低, 预估 token：~1500 / 无历史参考）
  - 覆盖：多条记录去重合并、空输入返回空集、重叠 phase 去重
  - 文件范围：`tests/test_duration_predictor.py`（新建）

- [ ] 2. 编写 `_predict_phase` 测试组（预估复杂度：中, 预估 token：~2000 / 无历史参考）
  - 覆盖：不足 3 条记录时中位数回退、零记录返回 DEFAULT_PHASE_SECONDS (30.0)、回归结果负值钳位 >= 0.0
  - 文件范围：`tests/test_duration_predictor.py`（追加）

- [ ] 3. 编写 `_fallback_estimates` 测试组（预估复杂度：低, 预估 token：~1500 / 无历史参考）
  - 覆盖：中位数估算 + `_total` 求和、空统计返回 `{"_total": 0.0}`、`_total` 等于各阶段估算之和
  - 文件范围：`tests/test_duration_predictor.py`（追加）

- [ ] 4. 验证全部测试通过 pytest + ruff（预估复杂度：低, 预估 token：~500 / 无历史参考）
  - `python -m pytest tests/test_duration_predictor.py` 退出码 0
  - `ruff check tests/test_duration_predictor.py` 无错误

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，覆盖 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个当前零覆盖函数
- 每个函数至少 2 个测试场景，总计至少 6 个 `def test_` 函数
- 测试可独立运行，不依赖运行时环境或外部服务

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有的 `tests/test_phase_duration.py`（该文件已覆盖 `_fit_linear` 和 `predict_change_duration`，功能不重叠）
- 不覆盖 `_fit_linear` 和 `predict_change_duration`（已有 `test_phase_duration.py` 覆盖）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块可正常 import
- `statistics.median` 标准库可用（无第三方依赖）
- `DEFAULT_PHASE_SECONDS = 30.0` 常量值稳定

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且 ruff check 通过
2. 包含 `test__collect_known_phases`、`test__predict_phase`、`test__fallback_estimates` 至少 3 个函数（实际目标 ≥6 个 test_ 函数）
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0，所有测试通过
4. 新测试与已有 `tests/test_phase_duration.py` 无功能重叠

### 验收方式
- `test -f tests/test_duration_predictor.py` 验证文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` ≥ 3
- `python -m pytest tests/test_duration_predictor.py -v` 退出码 0
- `ruff check tests/test_duration_predictor.py` 无输出

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析）
- `tests/test_phase_duration.py`（已有测试，不碰）
- 任何 `zsiga/` 目录下的源码文件

### 项目部署分支
- deploy

### 已知风险
- **僵尸提案循环**：此 proposal 已迭代 13+ 轮全部被 archive/skipped，测试文件从未持久化。执行时需确保文件实际写入磁盘并保留
- **文件名匹配 bug**：`_scan_code_structure()` 将 `test_phase_duration.py` 提取为 `"phase_duration"` 而非 `"duration_predictor"`，导致引擎反复误判"无测试"。本文件落地后此问题仍可能触发重复提案
- **与现有测试共存**：新文件 `test_duration_predictor.py` 将与 `test_phase_duration.py` 并存，需明确分工避免混淆

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（所有历史尝试均未落地执行）
