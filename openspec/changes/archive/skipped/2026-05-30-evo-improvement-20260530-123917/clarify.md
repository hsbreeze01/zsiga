# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数）创建专属测试文件 `tests/test_duration_predictor.py`。现有测试 `tests/test_phase_duration.py` 仅覆盖了 `_fit_linear`（正常路径）和 `predict_change_duration`（公开入口），三个私有函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）完全未测试。

### 拆解后的子任务

- [ ] 1. **私有辅助函数测试组**：`_collect_known_phases` + `_fallback_estimates` (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - `_collect_known_phases`：空输入、缺失 `phases` key、正常去重提取
  - `_fallback_estimates`：空输入、单条记录、多条记录中位数计算、sorted keys 输出
  - 文件范围：`tests/test_duration_predictor.py`（新建），import 自 `zsiga.duration_predictor`

- [ ] 2. **核心预测逻辑测试组**：`_predict_phase` (预估复杂度：中, 预估 token：~2000 / 无历史参考)
  - <3 样本回退中位数、负值截断到 0、正常回归预测、边界参数（零值 project_lines/proposal_chars）
  - 文件范围：`tests/test_duration_predictor.py`

- [ ] 3. **`_fit_linear` 退化场景补充测试** (预估复杂度：低, 预估 token：~1000 / 无历史参考)
  - 与 `test_phase_duration.py` 中已有的 `TestFitLinear` 互补，覆盖退化 case：共线输入、全相同输入、零向量
  - 文件范围：`tests/test_duration_predictor.py`

- [ ] 4. **验收验证**：运行 pytest 确认全部通过 + ruff lint 无错误 (预估复杂度：低, 预估 token：~500 / 无历史参考)
  - `python -m pytest tests/test_duration_predictor.py` 退出码 0
  - `ruff check tests/test_duration_predictor.py` 无错误

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的单元测试
- 补充 `_fit_linear` 的退化场景测试（与已有 `test_phase_duration.py` 互补，不重复覆盖正常路径）
- 通过 `from zsiga.duration_predictor import _collect_known_phases, _predict_phase, _fallback_estimates, _fit_linear` 导入私有函数

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有的 `tests/test_phase_duration.py`
- 不覆盖 `predict_change_duration`（已在 `test_phase_duration.py` 中充分覆盖）
- 不修改 pipeline/evolution 引擎代码

### 依赖的外部条件
- `zsiga/duration_predictor.py` 保持当前 API 不变（5 个函数签名稳定）
- Python ≥ 3.10 环境，pytest 可用
- 私有函数以 `_` 前缀命名，需通过模块路径直接 import（项目已有先例：`test_phase_duration.py` 中 `from zsiga.duration_predictor import _fit_linear`）

## 目标

### 成功标准
1. 文件 `tests/test_duration_predictor.py` 存在且包含 ≥ 3 个 `def test_` 函数
2. 测试文件中存在 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个函数名
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. `ruff check tests/test_duration_predictor.py` 无错误
5. 新测试与已有 `tests/test_phase_duration.py` 不冲突、不重复

### 验收方式
- `test -f tests/test_duration_predictor.py && echo "exists"`
- `grep -c "def test_" tests/test_duration_predictor.py` ≥ 3
- `grep -q "test__collect_known_phases" tests/test_duration_predictor.py`
- `grep -q "test__fit_linear" tests/test_duration_predictor.py`
- `grep -q "test__predict_phase" tests/test_duration_predictor.py`
- `python -m pytest tests/test_duration_predictor.py -v --tb=short`
- `ruff check tests/test_duration_predictor.py`

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（只读取分析，不修改）
- `tests/test_phase_duration.py`（已有测试，不修改）
- `zsiga/intake/evolution.py`（proposal 生成引擎，不在 scope 内）

### 项目部署分支
deploy

### 已知风险
- **僵尸循环**：此 proposal 已迭代 15+ 轮全部 skipped/archived，从未成功落地。本轮必须确保 `tests/test_duration_predictor.py` 实际写入磁盘并持久化
- **与已有测试重叠**：`tests/test_phase_duration.py` 已覆盖 `_fit_linear` 正常路径和 `predict_change_duration`，新文件应聚焦未覆盖的 3 个私有函数，避免重复
- **私有函数 import**：所有目标函数以 `_` 开头，需确认 `from zsiga.duration_predictor import _xxx` 可用（已有先例确认可行）

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（前 15+ 轮均未执行到实现阶段）
