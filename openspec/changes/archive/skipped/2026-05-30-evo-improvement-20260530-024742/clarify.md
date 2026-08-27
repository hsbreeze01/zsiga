# clarify.md — add-tests-runner

> ⚠️ **重大事实冲突**：proposal 声称 `zsiga/harness/runner.py` "缺少测试文件"，但
> `tests/test_harness_runner.py` **已经存在**（277 行、15+ test 函数），全面覆盖了
> runner.py 的全部 10 个类（TestEvent/TestStarted/TestPassed/TestFailed/TestError/
> HarnessResult/HarnessRunner/TestReport/QualificationReport/_HarnessCollectorPlugin）。
> 静态分析仅检查了 `test_runner.py` 文件名，遗漏了实际存在的 `test_harness_runner.py`。
> 以下拆解仍按 proposal 原文展开，但建议 steward 在审阅时重点关注此冲突。

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py`（352 行，10 个 dataclass/class）创建 `tests/test_runner.py`，提供模块导入验证和冒烟测试。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_runner.py` 基础骨架与导入测试 (预估复杂度：低, 预估 token：~800)
  - 文件范围：`tests/test_runner.py`（新建）
  - 内容：`test_module_import` 验证 `zsiga.harness.runner` 可导入；`test_module_smoke` 验证关键类（TestEvent, HarnessResult, HarnessRunner 等）可实例化
  - ⚠️ 注意：这将与已有的 `tests/test_harness_runner.py`（277 行、20+ 用例）形成冗余覆盖

- [ ] 2. 确认 pytest 执行通过 (预估复杂度：低, 预估 token：~200)
  - 文件范围：`tests/test_runner.py`
  - 内容：`python -m pytest tests/test_runner.py` 退出码为 0，且不破坏现有测试套件

## 边界

### IN scope
- 新建 `tests/test_runner.py`，包含 `test_module_import` 和 `test_module_smoke`
- 验证新建文件可通过 pytest

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改已有的 `tests/test_harness_runner.py`
- 不覆盖 `_HarnessCollectorPlugin` 内部 pytest hook 行为、`_append_jsonl()` 等（这些属于已有测试的增量补充范畴）

### 依赖的外部条件
- `zsiga/harness/runner.py` 保持当前结构不变
- pytest 可正常运行
- 已有 `tests/test_harness_runner.py` 不受影响

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在且包含 `test_module_import`、`test_module_smoke` 两个测试函数
2. `python -m pytest tests/test_runner.py` 退出码 0
3. 新建文件不引入与 `tests/test_harness_runner.py` 的命名冲突或 import 冲突

### 验收方式
- `test -f tests/test_runner.py` 确认文件存在
- `grep -c 'def test_' tests/test_runner.py` 确认 ≥ 1 个测试函数
- `python -m pytest tests/test_runner.py -q` 退出码 0
- `python -m pytest tests/test_harness_runner.py -q` 退出码仍为 0（回归检查）

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`
- `tests/test_harness_runner.py`（已有 277 行完整覆盖）
- `tests/conftest_zsiga.py`
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- deploy

### 已知风险
- **冗余风险（高）**：`tests/test_harness_runner.py` 已全面覆盖 runner.py 的 10 个类。新建 `tests/test_runner.py` 仅提供 import/smoke 级别测试，价值极低，且两个文件并存会造成维护者困惑——"哪个是主测试文件？"
- **自演进引擎循环（高）**：此 proposal 模式（`add-tests-runner`）已被 skip/reject 26+ 次，是典型的空转循环。静态分析只匹配 `test_{module_basename}.py` 文件名，忽略了 `test_harness_runner.py` 这类按模块完整路径命名的文件
- **命名冲突（低）**：两个文件中可能出现同名测试函数（如都叫 `test_harness_result`），虽 pytest 允许但增加维护负担

### 预估 token 消耗
- prompt: ~1500
- completion: ~600
- 数据来源: 无历史参考（此前 26+ 次均为 skip/reject，无执行记录）
