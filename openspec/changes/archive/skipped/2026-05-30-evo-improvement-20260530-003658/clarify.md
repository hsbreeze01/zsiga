# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为无测试模块 `zsiga/duration_predictor.py`（164 行，5 个纯函数，0 类）创建单元测试文件 `tests/test_duration_predictor.py`，覆盖所有函数的核心路径。模块为纯数学/数据计算逻辑（线性回归、中位数估算、阶段预测），无外部 I/O 依赖，可直接测试无需 mock。

### 拆解后的子任务

- [ ] 1. **测试 `_collect_known_phases` + `_fit_linear` 基础函数** (预估复杂度：低, 预估 token：~2000)
   - 文件范围：`tests/test_duration_predictor.py`（新建）
   - `_collect_known_phases`：空输入→空集、多记录合并去重、缺失 `phases` key 跳过（3 场景）
   - `_fit_linear`：空输入→零向量、退化共线→均值回退、合成数据精确恢复系数（3 场景）

- [ ] 2. **测试 `_predict_phase` + `_fallback_estimates` 中间层函数** (预估复杂度：中, 预估 token：~3000)
   - 文件范围：`tests/test_duration_predictor.py`
   - `_predict_phase`：无匹配记录→DEFAULT、<3 数据→中位数、≥3 数据→回归、负值钳位为 0（4 场景）
   - `_fallback_estimates`：空输入→`{_total:0}`、有/无数据混合、`_total` 与各阶段之和一致（3 场景）

- [ ] 3. **测试 `predict_change_duration` 公共入口函数** (预估复杂度：中, 预估 token：~2500)
   - 文件范围：`tests/test_duration_predictor.py`
   - <3 记录→委托 fallback、≥3 记录→逐阶段回归、`_total` 一致性、输入边界（4 场景）

- [ ] 4. **验证全部测试通过 + lint 干净** (预估复杂度：低, 预估 token：~500)
   - 运行 `python -m pytest tests/test_duration_predictor.py` 确认退出码 0
   - 运行 `ruff check tests/test_duration_predictor.py` 确认无 lint 错误

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，覆盖 5 个函数的 17 个测试场景
- 测试可独立运行，不依赖运行时环境（无 LLM、无文件 I/O、无 subprocess）
- 遵循项目现有测试模式（参考 `tests/test_harness_runner.py` 等文件的写法风格）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改 `zsiga/` 下任何其他文件
- 不添加新的依赖包
- 不涉及 CI/CD 配置变更
- 不修改 `conftest.py` 或其他测试基础设施

### 依赖的外部条件
- `zsiga/duration_predictor.py` 的 5 个函数签名和语义保持稳定
- 项目 Python 环境 >=3.10 且 pytest 可用
- 被测模块无外部依赖（纯 stdlib `statistics` + 基础数学运算），无需 mock

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 存在且包含 ≥3 个 `def test_` 函数
2. 覆盖全部 5 个函数（`_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration`）
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. `ruff check tests/test_duration_predictor.py` 无错误
5. 测试函数名包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase`

### 验收方式
- 文件存在性检查：`test -f tests/test_duration_predictor.py`
- 函数名检查：`grep -c 'def test_' tests/test_duration_predictor.py` ≥ 3
- pytest 通过：`python -m pytest tests/test_duration_predictor.py` 退出码 0
- lint 通过：`ruff check tests/test_duration_predictor.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（只读分析，不做任何修改）
- `zsiga/` 下所有其他源码文件
- `tests/conftest.py`、`tests/conftest_zsiga.py`
- `pyproject.toml`、`requirements.txt`
- `zsiga.yaml`

### 项目部署分支
- deploy（根据 `zsiga.yaml` 中 `project=zsiga` 目标的 `deploy_branch` 配置）

### 已知风险
- **历史失败记录**：`changes/archive/` 下有 8 个历史迭代（`20260527`~`20260528`）均未成功落地，需确保本次测试用例设计稳健，避免因边界条件处理不当导致测试 flaky
- `_fit_linear` 函数含矩阵运算和退化分支（共线检测），测试数据需精确构造以确保断言可靠
- 私有函数（`_` 前缀）测试通过 `from zsiga.duration_predictor import _fn` 导入，需确认模块未使用 `__all__` 限制导出

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类任务 `test_harness_runner.py` 277 行可做参照，但本次目标模块仅 164 行、纯函数，预计测试文件 ~120-180 行）
