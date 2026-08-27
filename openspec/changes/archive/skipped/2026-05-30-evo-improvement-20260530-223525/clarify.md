# clarify.md — add-tests-runner

> ⚠️ **关键预警**：此 proposal 的核心前提已被确认为**虚假**。
> `tests/test_harness_runner.py`（277 行，20 个测试方法，5 个测试类）**已存在且完整覆盖** `zsiga/harness/runner.py` 的全部 10 个类。
> 此 proposal 已被引擎生成 37+ 次，全部被 skip/reject。根因是 `evolution.py` 的 `_scan_code_structure()` 用 basename 匹配文件名，
> `runner` ≠ `harness_runner`，导致引擎永远"看不到"已有测试文件。

---

## 需求拆解

### 原始需求
为无测试模块 `zsiga/harness/runner.py`（352 行，10 个类）添加单元测试覆盖，创建 `tests/test_runner.py`。

### 拆解后的子任务

- [ ] 1. 确认已有测试覆盖情况 (预估复杂度：低, 预估 token：~500 / 无历史参考)
  - 审计 `tests/test_harness_runner.py` 的 20 个测试方法，确认覆盖的类/方法
  - 与 `runner.py` 的 10 个类做 gap analysis
- [ ] 2. 评估增量价值并决定是否创建 `tests/test_runner.py` (预估复杂度：低, 预估 token：~500 / 无历史参考)
  - 若已有覆盖完整 → 停止，标记为已完成（REJECT 此 change）
  - 若存在真实 gap → 在 clarify 中明确增量范围后继续

**结论：子任务 1 的审计结果已由并行探索确认 — 覆盖完整，无增量价值。**

---

## 边界

### IN scope
- 为 `zsiga/harness/runner.py` 的公开类编写测试（proposal 原始意图）

### OUT of scope
- 修改 `zsiga/harness/runner.py` 源码
- 修改 `evolution.py` 的 `_scan_code_structure()` basename 匹配逻辑（这是真正的 bug，但不在本 change scope 内）
- 删除或重构已有的 `tests/test_harness_runner.py`

### 依赖的外部条件
- `tests/test_harness_runner.py` 已存在并覆盖全部 10 个类（**已确认满足**）
- `zsiga/harness/runner.py` 无 lint 问题（**已确认**）

---

## 目标

### 成功标准
1. `zsiga/harness/runner.py` 的所有公开类有单元测试覆盖
2. 测试可通过 `pytest` 执行且退出码 0

### 验收方式
- **已有文件验证**：`tests/test_harness_runner.py` 存在且包含 `TestEventDataclasses`、`TestHarnessResult`、`TestHarnessRunnerDiscover`、`TestHarnessRunnerRun`、`TestHarnessRunnerPytestFailClosed` 五个测试类
- **运行验证**：`python -m pytest tests/test_harness_runner.py` 退出码 0
- ⚠️ BAC-01~BAC-04 要求创建 `tests/test_runner.py`，但该文件将与已有测试**完全冗余**

---

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（仅读取分析，不修改）
- `tests/test_harness_runner.py`（已有完整覆盖，不应破坏）

### 项目部署分支
- deploy

### 已知风险
- **重复文件风险**：创建 `tests/test_runner.py` 将产生与 `test_harness_runner.py` 功能完全重叠的冗余文件，增加维护成本和混淆
- **循环生成风险**：此 proposal 已被生成 37+ 次均被 reject，继续执行不会终止循环，反而可能鼓励引擎继续生成
- **根因未修复**：真正的 bug 在 `zsiga/intake/evolution.py` 的 `_scan_code_structure()` basename 匹配逻辑（`"runner"` ≠ `"harness_runner"`），不修复该 bug 则类似 proposal 会无限循环

### 预估 token 消耗
- prompt: ~1500
- completion: ~500
- 数据来源: 无历史参考（因同类 proposal 全部被 reject，无成功交付记录）

### 建议
**REJECT 此 change**。真正的修复应为：
1. 修复 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的测试文件发现逻辑（将 basename 匹配改为更灵活的包含匹配）
2. 将 `add-tests-runner` 加入 proposal 黑名单，阻止重复生成
