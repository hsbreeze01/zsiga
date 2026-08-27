# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为无测试模块 `zsiga/duration_predictor.py`（164 行、5 函数、0 类、平均 CC 4.8、无高复杂度函数）添加单元测试文件 `tests/test_duration_predictor.py`，覆盖全部 5 个函数的行为。模块只有 1 个公开入口 `predict_change_duration`，其余 4 个为私有辅助函数，但均可通过直接导入测试。

### 拆解后的子任务

- [ ] 1. **测试 `_collect_known_phases`** — 验证从 `phase_stats` 字典中提取已知阶段的逻辑，覆盖空输入、单阶段、多阶段场景（预估复杂度：低，预估 token：~800）
- [ ] 2. **测试 `_fit_linear`** — 验证线性拟合核心算法，覆盖正常拟合（多数据点）、退化情况（少于 2 个点）、边界值（全零/全相同值）（预估复杂度：中，预估 token：~1500）
- [ ] 3. **测试 `_predict_phase`** — 验证单阶段预测逻辑，覆盖有历史记录时的预测路径和无历史时的回退路径（预估复杂度：低，预估 token：~1000）
- [ ] 4. **测试 `_fallback_estimates`** — 验证回退估算生成逻辑，覆盖空 stats 和包含部分阶段 stats 的场景（预估复杂度：低，预估 token：~800）
- [ ] 5. **测试 `predict_change_duration`（公开入口）** — 验证顶层编排函数，覆盖完整预测流程和回退流程的集成（预估复杂度：中，预估 token：~1200）

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 为全部 5 个函数编写单元测试（含 4 个私有函数 + 1 个公开函数）
- 使用 mock 隔离必要的内部依赖

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改其他测试文件或配置文件
- 不涉及性能测试或集成测试

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块存在且 API 稳定（164 行，5 函数）
- 项目 pytest 基础设施可用（`tests/conftest_zsiga.py`）
- 所有依赖可在当前 Python 环境中导入（纯计算模块，无 LLM/IO 依赖）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含至少 5 个 `def test_` 函数
2. 测试覆盖全部 5 个函数：`_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration`
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0，无失败/错误
4. 测试不依赖运行时环境（无文件 I/O、无网络、无 LLM 调用）

### 验收方式
- BAC-01: `tests/test_duration_predictor.py` 文件存在 ✓
- BAC-02: 文件中包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 函数定义 ✓
- BAC-03: 文件中包含至少 3 个 `def test_` 函数 ✓
- BAC-04: `python -m pytest tests/test_duration_predictor.py` 退出码 0 ✓

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py` — 仅读取分析，不做任何修改
- `tests/conftest_zsiga.py` — 不修改现有 conftest
- `pyproject.toml`、`requirements.txt` — 不修改项目配置

### 项目部署分支
- `main`

### 已知风险
- 模块含 4 个私有函数（`_` 前缀），测试需直接导入私有符号，未来版本可能重命名
- `_fit_linear` 是最长函数（54 行），内部可能有数值计算边界情况需仔细构造测试数据
- 此 proposal 由自演进引擎生成，静态分析数据已验证（行数、函数数、CC 均合理）

### 预估 token 消耗
- prompt: ~5000
- completion: ~3000
- 数据来源: 无历史参考（duration_predictor 模块首次添加测试）
