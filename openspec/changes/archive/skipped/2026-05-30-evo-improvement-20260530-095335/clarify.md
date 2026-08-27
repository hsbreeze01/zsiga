# clarify.md — # add-tests-runner

> **⚠️ 关键风险警告**: 此 proposal 的核心前提已被多次验证为**事实性错误**。
> `tests/test_harness_runner.py`（277 行，6 个测试类，20+ test 方法）已完整覆盖
> `zsiga/harness/runner.py` 的全部 10 个公开符号。此 proposal 已被引擎生成 27+ 次，
> 全部被 skip/reject。创建 `tests/test_runner.py` 将产生冗余测试文件。
> 根因是 `zsiga/intake/evolution.py` 的 `_scan_code_structure()` 使用
> `os.path.basename()` 匹配测试文件名（`runner` ≠ `harness_runner`）。

---

## 需求拆解

### 原始需求

为模块 `zsiga/harness/runner.py`（352 行，10 个类）创建单元测试文件 `tests/test_runner.py`，
覆盖公开函数和类，使用 mock 隔离外部依赖，确保每个测试可独立运行。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_runner.py` 基础骨架 — 包含模块导入验证 (`test_module_import`) 和冒烟测试 (`test_module_smoke`)（预估复杂度：低, 预估 token：~1500 / 无有效历史参考 — 历史 27+ 次均未成功交付）
- [ ] 2. 编写事件 dataclass 测试 — 覆盖 `TestEvent`, `TestStarted`, `TestPassed`, `TestFailed`, `TestError` 的构造与字段默认值（预估复杂度：低, 预估 token：~2500 / 无有效历史参考）
- [ ] 3. 编写 `HarnessResult` 和报告类测试 — 覆盖 `HarnessResult`, `TestReport`, `QualificationReport` 的聚合逻辑与字段（预估复杂度：低, 预估 token：~2000 / 无有效历史参考）
- [ ] 4. 编写 `HarnessRunner` 核心方法测试 — 覆盖 `discover()`, `run()`, `run_pytest()` 等，使用 mock 隔离 subprocess/文件系统依赖（预估复杂度：中, 预估 token：~3000 / 无有效历史参考）

---

## 边界

### IN scope
- 新建 `tests/test_runner.py` 文件
- 为 `zsiga/harness/runner.py` 中的 10 个类编写单元测试
- 使用 mock 隔离外部依赖（subprocess、文件 I/O）
- 满足 BAC-01 ~ BAC-04 四条验收标准

### OUT of scope
- 不修改 `zsiga/harness/runner.py` 源码
- 不修改 `tests/test_harness_runner.py`（已存在的完整测试文件）
- 不修复 `zsiga/intake/evolution.py` 中的 basename 匹配 bug（真正的根因）
- 不删除或归档 archive 中的历史冗余 proposal

### 依赖的外部条件
- `zsiga/harness/runner.py` 模块结构保持不变（10 个类，352 行）
- pytest 可正常执行且 `tests/test_harness_runner.py` 通过（已有测试不能被破坏）
- 新文件 `tests/test_runner.py` 不与 `tests/test_harness_runner.py` 产生 import 冲突或 fixture 冲突

---

## 目标

### 成功标准
1. 文件 `tests/test_runner.py` 存在且包含 `test_module_import` 和 `test_module_smoke` 函数
2. `tests/test_runner.py` 包含至少 1 个 `def test_` 函数（proposal 要求 ≥1，实际需要覆盖 10 个类）
3. `python -m pytest tests/test_runner.py` 退出码为 0
4. `python -m pytest tests/test_harness_runner.py` 退出码仍为 0（不破坏已有测试）

### 验收方式
- 运行 `python -m pytest tests/test_runner.py -v` 确认退出码 0
- 运行 `python -m pytest tests/test_harness_runner.py -v` 确认已有测试未受影响
- 检查新文件中 `def test_` 函数数量 ≥ 1（BAC-03）
- 静态检查文件存在性（BAC-01）和符号存在性（BAC-02）

---

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析）
- `tests/test_harness_runner.py`（已有完整覆盖，不可破坏）
- `zsiga/intake/evolution.py`（basename bug 修复不在 scope 内）

### 项目部署分支
- deploy（根据项目配置 `targets.zsiga.deploy_branch`）

### 已知风险
- **冗余覆盖风险（严重）**: `tests/test_harness_runner.py` 已有 20+ 测试全面覆盖 `runner.py` 的全部 10 个类。新建 `tests/test_runner.py` 将产生两个文件测试同一模块的混乱局面，增加维护负担。
- **Zombie loop 风险（严重）**: 此 proposal 已被引擎生成 27+ 次并全部 skip/reject。即使本轮成功交付，引擎仍会因 basename bug 继续生成同名 proposal。
- **proposal 静态分析数据失真**: proposal 声称"函数数: 0"、所有类 `methods=[]`，实际 `HarnessRunner` 有 `discover()`/`run()`/`run_pytest()` 等多个方法。实施者需自行分析源码获取真实 API。
- **BAC 标准过低**: BAC-03 仅要求 ≥1 个 `def test_` 函数，不保证有意义的覆盖度。
- **fixture 冲突风险**: 两个测试文件可能通过 `conftest.py` 共享 fixture，需确保无命名冲突。

### 预估 token 消耗
- prompt: ~8000（源码分析 + 测试设计上下文）
- completion: ~4000（测试代码生成）
- 数据来源: 无历史参考 — 27+ 次历史尝试均未成功交付，无有效基线数据
