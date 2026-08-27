# clarify.md — add-tests-runner

> ⚠️ **核心前提已被多次验证为事实性错误**。本 clarify 忠实记录 proposal 内容，但标注关键事实矛盾。

## 需求拆解

### 原始需求
Proposal 声称为"无测试模块" `zsiga/harness/runner.py` (352 行, 10 类) 创建测试文件 `tests/test_runner.py`，提供单元测试覆盖。

### 事实核查（关键矛盾）

| proposal 声称 | 实际情况 |
|---|---|
| "缺少测试文件 `tests/test_runner.py`" | `tests/test_harness_runner.py` **已存在**（277 行，6 个测试类，20+ 测试方法），完整覆盖全部 10 个公开符号 |
| "函数数: 0" | HarnessRunner 类含 `discover()`、`run()`、`run_pytest()` 等多个方法 |
| "methods=[]"（所有类） | 静态分析数据严重失真，event dataclass 有字段，HarnessRunner 有多个方法 |

**根因**：`zsiga/intake/evolution.py` L1092-1098 的 `_scan_code_structure()` 使用 `os.path.basename()` 提取模块名 → `runner` ≠ `harness_runner`（测试文件去掉 `test_` 前缀后的值），匹配永远失败，引擎误判为"无测试"。

**此 proposal 已被生成 27+ 次，全部被 skip/reject，是已确认的 zombie loop。**

### 拆解后的子任务
- [ ] 1. 创建 `tests/test_runner.py` 并编写导入/冒烟测试 (预估复杂度：低, 预估 token：~2000 / 无历史参考 — 因从未成功交付)
- [ ] 2. 为 `zsiga/harness/runner.py` 中 10 个类编写单元测试 (预估复杂度：中, 预估 token：~4000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_runner.py`
- 覆盖 `zsiga/harness/runner.py` 中的公开类和函数（仅读取分析，不修改源码）

### OUT of scope
- 不修改 `zsiga/harness/runner.py`
- 不修改 `zsiga/intake/evolution.py` 的 basename 匹配 bug（**但这是真正需要修复的问题**）
- 不修改或合并 `tests/test_harness_runner.py`（已存在的完整测试文件）

### 依赖的外部条件
- ⚠️ **存在同名已有测试文件**：`tests/test_harness_runner.py` 已覆盖全部目标符号，新文件将与已有测试完全重复
- ⚠️ **27+ 轮空转风险**：同题 proposal 历史成功率 0%，执行后大概率被 skip

## 目标

### 成功标准
1. `tests/test_runner.py` 文件存在
2. 文件内包含 `test_module_import`、`test_module_smoke` 函数
3. 包含至少 1 个 `def test_` 函数
4. `python -m pytest tests/test_runner.py` 退出码 0

### 验收方式
- 文件存在性检查：`test -f tests/test_runner.py`
- pytest 执行：`python -m pytest tests/test_runner.py -v`
- 符号检查：grep `test_module_import` / `test_module_smoke`

**⚠️ 即使全部 BAC 通过，产出也是一个与 `tests/test_harness_runner.py` 完全冗余的文件，不产生实际质量价值。**

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（源码不可动）
- `tests/test_harness_runner.py`（已有测试不可动）
- `zsiga/intake/evolution.py`（basename 匹配 bug 不可在此 proposal scope 内修复）

### 项目部署分支
deploy

### 已知风险
- **zombie loop 风险（极高）**：此 proposal 已循环 27+ 次，每次生成 → clarify → skip/reject，零次成功交付。接受此 proposal 只会开始第 28 轮空转
- **冗余测试文件**：`tests/test_harness_runner.py` 已完整覆盖目标模块，新建 `tests/test_runner.py` 将导致两个文件测试同一模块
- **静态分析数据失真**：proposal 提供的类方法列表全为空、函数数为 0，无法作为实施指导
- **真正需要修复的是引擎 bug**：`evolution.py` 的 `os.path.basename()` 匹配逻辑应改为支持子路径匹配（如 `harness/runner` → `harness_runner`）

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（从未成功交付过）
