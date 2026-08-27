# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个纯函数）创建单元测试文件 `tests/test_duration_predictor.py`，覆盖所有公开和内部函数的核心路径。该模块负责基于历史 `phase_stats` 数据预测变更各阶段耗时，全部为纯计算函数，无外部依赖需要 mock。

### 拆解后的子任务

- [ ] 1. **测试数据 fixtures 与辅助工具** — 构建 `phase_stats` 样本数据集（充足数据 ≥3 条 / 不足数据 <3 条 / 空数据），定义可复用的 pytest fixtures。预估复杂度：低，预估 token：~1500
- [ ] 2. **纯提取/回退函数测试** — 覆盖 `_collect_known_phases()`（从 phase_stats 提取阶段名集合）和 `_fallback_estimates()`（数据不足时的中位数回退逻辑），包含边界用例（空列表、单条记录、缺失阶段字段）。预估复杂度：低，预估 token：~2000
- [ ] 3. **线性回归与预测函数测试** — 覆盖 `_fit_linear()`（最小二乘拟合、退化输入）和 `_predict_phase()`（充足数据走回归 / 不足走回退），以及主入口 `predict_change_duration()`（集成所有子函数，验证返回结构含 `_total` 字段且值等于各阶段之和）。预估复杂度：中，预估 token：~3000

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含针对 5 个函数的单元测试
- 覆盖正常路径、边界条件（空数据、单条记录、缺失字段）
- 验证 `predict_change_duration()` 返回结构（各阶段 key + `_total` 求和一致性）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有测试 `tests/test_phase_duration.py`（已覆盖公开 API 的集成层面测试）
- 不涉及 `metrics/collector.py`、`metrics/types.py`、`metrics/db.py` 等上游模块

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块可正常 import（无外部依赖，纯计算）
- pytest 运行环境可用

### ⚠️ 关键风险提示
探索报告显示 `tests/test_phase_duration.py`（241 行）已存在，声称覆盖 duration predictor 的公开 API。执行前需确认该文件的实际覆盖范围，避免创建功能完全重叠的测试文件。如果已有测试已充分覆盖所有 5 个函数，此 proposal 的价值将大幅降低。

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 ≥5 个 `def test_` 函数
2. 覆盖全部 5 个目标函数：`_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration`
3. 包含边界条件测试（空数据、单条记录、数据不足 <3 条的回退路径）
4. `python -m pytest tests/test_duration_predictor.py` 退出码 0
5. 新测试与已有 `tests/test_phase_duration.py` 不产生 import 冲突或 fixture 名冲突

### 验收方式
- `test -f tests/test_duration_predictor.py` 文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 计数 ≥ 5
- `grep -q 'test__collect_known_phases\|test__fit_linear\|test__predict_phase\|test__fallback_estimates\|test_predict_change_duration' tests/test_duration_predictor.py`
- `python -m pytest tests/test_duration_predictor.py -v` 全部 PASSED
- `python -m pytest tests/test_duration_predictor.py tests/test_phase_duration.py` 两者联合运行无冲突

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析，不做任何修改）
- `tests/test_phase_duration.py`（已有测试文件，不修改）
- `zsiga/metrics/` 下所有文件（上游模块，不在范围内）

### 项目部署分支
- `deploy`（主部署分支）

### 已知风险
- **测试重叠风险**：`tests/test_phase_duration.py`（241 行）可能已覆盖部分或全部目标函数。如果重叠度高，新文件的增量价值低，且增加维护负担。建议执行前先用 `grep` 确认已有测试的覆盖范围。
- **auto-generated proposal 历史风险**：自演进引擎生成的测试提案有多次因"测试已存在"被 REJECT 的记录（runner.py × 26+，config.py × 多次）。虽然本 proposal 的目标文件名确实不存在，但已有 `test_phase_duration.py` 可能覆盖同一模块。
- **私有函数测试稳定性**：`_collect_known_phases`、`_fit_linear` 等以下划线开头的函数属模块内部实现，测试它们增加了与实现细节的耦合度。

### 预估 token 消耗
- prompt: ~3000
- completion: ~4000
- 数据来源: 无历史参考（基于模块复杂度 164 行 / 5 函数 / 平均 CC 4.8 估算）
