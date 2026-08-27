# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
Proposal 声称为"无测试模块" `zsiga/harness/runner.py` 添加单元测试文件 `tests/test_runner.py`。

**但这是一个基于虚假前提的空转循环提案**，已被自演进引擎反复生成 26+ 次，全部被 skip/reject。实际测试文件 `tests/test_harness_runner.py`（277 行，28 个测试函数）已完整覆盖 `runner.py` 的全部公开 API。

### 拆解后的子任务

**本 proposal 不应执行。** 以下子任务描述的是真正应做的事——修复自演进引擎的测试发现逻辑，而非为已有测试的模块重复创建测试。

- [ ] 1. 修复 `zsiga/intake/evolution.py` 的测试文件发现逻辑：从仅匹配 `test_{module_basename}.py`（如 `test_runner.py`）改为遍历所有 `test_*.py` 并检查是否 import 目标模块 (预估复杂度：中, 预估 token：~6000 / 无历史参考)
- [ ] 2. 为修复后的发现逻辑添加防御性测试，确保 `test_harness_runner.py` 能被正确识别为 `harness/runner.py` 的测试文件 (预估复杂度：低, 预估 token：~3000 / 无历史参考)

## 边界

### IN scope
- 修复 `zsiga/intake/evolution.py` 中测试文件发现逻辑的命名匹配缺陷
- 为修复添加测试覆盖

### OUT of scope
- ❌ 创建 `tests/test_runner.py`（重复文件，`tests/test_harness_runner.py` 已存在且充分覆盖）
- ❌ 修改 `zsiga/harness/runner.py` 源码
- ❌ 修改 `tests/test_harness_runner.py` 现有测试

### 依赖的外部条件
- 需要定位 `zsiga/intake/evolution.py` 中生成测试 proposal 的具体函数（预计在 proposal 生成模板的静态分析阶段）
- 需确认现有 28 个测试全部通过（`python -m pytest tests/test_harness_runner.py`）

## 目标

### 成功标准
1. 自演进引擎在评估 `zsiga/harness/runner.py` 时，能正确识别 `tests/test_harness_runner.py` 为其测试文件，不再生成"缺少测试"的 proposal
2. 修复后的发现逻辑对其他模块（如 `config.py` 对应 `test_config_validation.py`）同样生效
3. 所有现有测试（`pytest tests/`）通过，ruff lint 无新增问题

### 验收方式
- `python -m pytest tests/` 退出码 0
- 手动触发 evolution cycle 后，不再产生 `add-tests-runner` 同名 proposal
- 新增测试验证：给定模块路径 `harness/runner.py` 和测试文件 `test_harness_runner.py`，发现函数返回 True

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（目标源码，不涉及）
- `tests/test_harness_runner.py`（已有测试，不涉及）
- `zsiga.yaml`（配置文件）

### 项目部署分支
- `deploy`（zsiga 项目的部署分支）

### 已知风险
- **空转循环风险**：本 proposal 本身是空转循环的产物，如按原始描述执行（创建 `test_runner.py`），只会产生与 `test_harness_runner.py` 重复的测试文件，增加维护负担
- **根因定位不确定性**：`evolution.py` 文件较大，测试发现逻辑的具体位置需在实施阶段精确定位
- **回归风险**：修改 evolution.py 的发现逻辑可能影响其他模块的 proposal 生成行为

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（修复 evolution 引理属新模式）
