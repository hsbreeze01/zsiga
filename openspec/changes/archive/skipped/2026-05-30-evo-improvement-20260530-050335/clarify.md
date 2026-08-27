# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（352 行，10 个 dataclass 类）创建 `tests/test_runner.py` 单元测试文件，覆盖公开 API（TestEvent 家族、HarnessResult、TestReport、QualificationReport、HarnessRunner）。

### ⚠️ 关键发现：需求前提不成立
`tests/test_harness_runner.py`（277 行，5 个测试类，18+ 测试方法）**已经存在且覆盖充分**。本 proposal 基于自演进引擎的静态分析缺陷——仅匹配 `test_{basename}.py`（即 `test_runner.py`），忽略了实际命名 `test_harness_runner.py`。此同名 proposal 已在 archive 中出现 **26+ 次**，全部被 skip/reject。

### 拆解后的子任务
- [ ] 1. 评估现有测试覆盖 vs proposal 目标，确认增量价值（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 2. 若确认有增量价值，在 `tests/test_harness_runner.py`（而非新建 `test_runner.py`）中补充缺失测试用例（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 3. 运行 pytest 验证所有测试通过，ruff 检查通过（预估复杂度：低, 预估 token：~500 / 无历史参考）

## 边界

### IN scope
- 评估 `tests/test_harness_runner.py` 对 `zsiga/harness/runner.py` 的覆盖充分性
- 若存在未覆盖 API，在现有测试文件中补充（而非新建文件）
- pytest + ruff 验证

### OUT of scope
- 新建 `tests/test_runner.py`（与现有 `test_harness_runner.py` 重复）
- 修改 `zsiga/harness/runner.py` 源码
- 修改 `zsiga/harness/__init__.py` 中高层函数（`run_capability_tests` 等）的测试

### 依赖的外部条件
- 现有测试文件 `tests/test_harness_runner.py` 可正确运行
- `zsiga/harness/runner.py` 模块可正常导入

## 目标

### 成功标准
1. **首要标准**：确认现有 `tests/test_harness_runner.py` 的覆盖情况，输出覆盖差距分析
2. 若存在未覆盖的公开 API，补充对应测试用例到现有文件中
3. 所有测试（含新增）通过 pytest，退出码 0
4. ruff lint 检查通过

### 验收方式
- 确认 `tests/test_harness_runner.py` 已覆盖 `runner.py` 的全部 10 个类
- 若补充测试：`python -m pytest tests/test_harness_runner.py` 退出码 0
- 若确认无需补充：记录覆盖分析结论，关闭此 proposal

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- 任何非测试文件

### 项目部署分支
deploy

### 已知风险
- **空转循环风险**：此 proposal 已被自动生成 26+ 次，全部被 skip/reject。本 clarify 首次将策略从"新建文件"调整为"评估现有覆盖"，旨在打破循环
- **重复测试风险**：若强行创建 `tests/test_runner.py`，将与 `test_harness_runner.py` 产生完全重叠，增加维护负担
- **静态分析缺陷**：proposal 中的"函数数: 0""无法提取函数列表"表明引擎对 dataclass 类的方法提取存在系统性 bug

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（此前 26+ 次均在 clarify 之前被 reject）
