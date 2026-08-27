# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数，0 个类）创建单元测试文件 `tests/test_duration_predictor.py`。该模块当前无专属测试文件，是覆盖缺口。注意 `tests/test_phase_duration.py`（241 行，7 个测试类）已部分覆盖 `_fit_linear` 和 `predict_change_duration`，新测试应聚焦未覆盖函数并补充边界场景，避免与已有测试大量重复。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_duration_predictor.py` 骨架，导入被测模块全部 5 个函数（含私有函数通过直接导入），编写 `test__collect_known_phases` 覆盖：空输入、单一阶段、多阶段去重 (预估复杂度：低, 预估 token：~2000)
- [ ] 2. 编写 `test__fit_linear` 补充 `tests/test_phase_duration.py` 未覆盖的边界场景：退化输入（零向量、共线点）、数值精度校验、单样本输入 (预估复杂度：中, 预估 token：~3000)
- [ ] 3. 编写 `test__predict_phase` 和 `test__fallback_estimates`，覆盖：足够样本走线性预测路径、样本不足走中位数回退、空 records 边界、`_fallback_estimates` 对各阶段的中位数计算 (预估复杂度：中, 预估 token：~3000)
- [ ] 4. 编写 `test_predict_change_duration` 集成测试，验证公开入口函数正确组合内部函数的返回结构，补充 `test_phase_duration.py` 未覆盖的分支 (预估复杂度：低, 预估 token：~2000)
- [ ] 5. 运行 `pytest tests/test_duration_predictor.py` + `ruff check`，确认全部通过且无 lint 问题 (预估复杂度：低, 预估 token：~1000)

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，覆盖 `zsiga/duration_predictor.py` 的 5 个函数
- 补充 `tests/test_phase_duration.py` 未覆盖的边界场景（如 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）
- 包含 BAC 要求的 3 个指定测试函数名：`test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改 `tests/test_phase_duration.py` 或其他已有测试文件
- 不添加 `conftest.py` 或修改项目配置

### 依赖的外部条件
- `zsiga/duration_predictor.py` 的 5 个函数签名和返回结构在实现期间不变
- `tests/test_phase_duration.py` 已有的测试不受新测试影响（无共享 fixture 冲突）
- pytest 和 ruff 在当前环境中可用

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 文件中存在 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个指定函数
3. `python -m pytest tests/test_duration_predictor.py` 退出码为 0
4. `ruff check tests/test_duration_predictor.py` 无错误
5. 新测试与 `tests/test_phase_duration.py` 已有测试无重复逻辑

### 验收方式
- `test -f tests/test_duration_predictor.py` 确认文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 确认 ≥ 3
- `grep 'def test__collect_known_phases\|def test__fit_linear\|def test__predict_phase' tests/test_duration_predictor.py` 确认 3 个函数名
- `python -m pytest tests/test_duration_predictor.py -v` 确认全部通过

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（只读分析）
- `tests/test_phase_duration.py`（已有测试，不碰）
- `pyproject.toml`、`requirements.txt`（不修改依赖）
- `tests/conftest_zsiga.py`（不修改公共 fixture）

### 项目部署分支
- deploy（根据项目配置，变更应提交到 deploy 分支）

### 已知风险
- **僵尸提案循环**：同名 `add-tests-duration_predictor` 已迭代 10+ 轮全部 archived/skipped。历史 pytest 缓存显示曾有可运行测试类（`TestCollectKnownPhases`、`TestFallbackEstimates` 等）但从未持久化。需确保测试文件写入后立即 pytest 验证，避免再次丢失。
- **与 test_phase_duration.py 重复**：该文件已覆盖 `_fit_linear` 和 `predict_change_duration` 部分路径，新测试需聚焦补充场景而非重复断言。
- **私有函数可测试性**：`_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates` 均为 `_` 前缀私有函数，需通过 `from zsiga.duration_predictor import _xxx` 直接导入测试。

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（10+ 轮均未到达实现阶段）
