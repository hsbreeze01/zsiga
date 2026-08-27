# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为无测试模块 `zsiga/duration_predictor.py`（164 行，5 个函数，平均 CC 4.8，无高复杂度函数）创建单元测试文件 `tests/test_duration_predictor.py`，覆盖所有公开/内部函数的核心逻辑路径。

### 拆解后的子任务

- [ ] 1. **纯函数单元测试** — 为 `_collect_known_phases`（过滤空 phase_stats）、`_fallback_estimates`（硬编码回退字典）编写测试，覆盖正常/空输入/None 边界（预估复杂度：低，预估 token：~1500）
- [ ] 2. **核心算法测试** — 为 `_fit_linear`（线性回归拟合，~54 行，模块最长函数）编写测试，覆盖正常拟合、单数据点、全零数据、极端值等场景（预估复杂度：中，预估 token：~2000）
- [ ] 3. **预测链路集成测试** — 为 `_predict_phase` 和 `predict_change_duration` 编写测试，验证从 phase_stats 到预测结果的完整链路，mock 底层 `_fit_linear` 的数学依赖（预估复杂度：中，预估 token：~2000）

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 覆盖 5 个函数：`_collect_known_phases`, `_fit_linear`, `_predict_phase`, `_fallback_estimates`, `predict_change_duration`
- 测试正常路径、边界输入（空 dict、None 字段、单条记录）、数学正确性

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改其他测试文件或 conftest
- 不涉及 LLM、文件 I/O、subprocess mock（该模块为纯数学/数据转换，无外部依赖）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 存在且函数签名与 proposal 描述一致
- pytest 运行环境可用（项目已有 `conftest_zsiga.py`）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在
2. 文件中包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个测试函数
3. 文件中包含至少 3 个 `def test_` 函数（实际目标：覆盖全部 5 个函数）
4. `python -m pytest tests/test_duration_predictor.py` 退出码 0，全部测试通过
5. `ruff check tests/test_duration_predictor.py` 无 lint 错误

### 验收方式
- `test -f tests/test_duration_predictor.py` 验证文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 计数 ≥ 3
- `grep -E 'def test__(collect_known_phases|fit_linear|predict_phase)' tests/test_duration_predictor.py` 验证 BAC-02 符号
- `python -m pytest tests/test_duration_predictor.py -v` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py` — 仅读取分析，不做任何修改
- `tests/conftest_zsiga.py` — 不修改现有 conftest

### 项目部署分支
- main

### 已知风险
- `_fit_linear` 是纯数学函数（54 行），测试需构造具体的 (xs1, xs2, ys) 输入并验证斜率/截距计算的正确性，需要理解其内部算法逻辑
- 此 proposal 由自演进引擎生成，静态分析数据（行号、函数签名）需在实施阶段与实际代码交叉验证
- 历史上有 `verify-layer0-with-tests` 在 verify 阶段失败的记录（模式：code.unknown），需确保测试不依赖运行时环境

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（该模块无同类测试先例，按 5 函数 × 2-3 场景估算）
