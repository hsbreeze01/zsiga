# clarify.md — add-tests-runner

> ⚠️ **致命缺陷警告**：此 proposal 的核心前提已被证伪。
> `tests/test_harness_runner.py`（277 行，28 个 test 函数）已完整覆盖 `zsiga/harness/runner.py`
> 的全部 10 个公开类（TestEvent/TestStarted/TestPassed/TestFailed/TestError/HarnessResult/
> TestReport/QualificationReport/HarnessRunner/_HarnessCollectorPlugin）。
> 此 proposal 是自演进引擎 `_scan_code_structure()` basename 匹配 bug 的产物，已生成 27+ 次并全部 skip/reject。

## 需求拆解

### 原始需求
Proposal 声称为无测试模块 `zsiga/harness/runner.py`（352 行，10 类）创建单元测试文件 `tests/test_runner.py`。

**事实核查**：该需求的前提——"模块缺少测试文件"——**不成立**。`tests/test_harness_runner.py` 已存在且覆盖完整。

### 拆解后的子任务

- [ ] 1. ❌ 不应执行 — 创建 `tests/test_runner.py` 将与 `tests/test_harness_runner.py` 完全冗余（预估复杂度：无，应跳过）

### 真正应解决的问题（proposal 未涵盖）

- [ ] A. 修复 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的 basename 匹配 bug（L1090-L1093），使引擎能正确识别 `test_harness_runner.py` 覆盖了 `harness/runner.py`（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] B. 将 `add-tests-runner` 加入引擎 proposal 黑名单，终止循环生成（预估复杂度：低, 预估 token：~500 / 无历史参考）

## 边界

### IN scope
- （proposal 原始 scope）为 `zsiga/harness/runner.py` 编写测试 → **已被现有文件覆盖，无需执行**

### OUT of scope
- 修改 `zsiga/harness/runner.py` 源码
- 修改 `tests/test_harness_runner.py`（现有测试文件）

### 依赖的外部条件
- 引擎 basename 匹配 bug 未修复 → 此 proposal 将持续被循环生成

## 目标

### 成功标准
1. ❌ ~~`tests/test_runner.py` 存在~~ — 不应创建冗余文件
2. ✅ `tests/test_harness_runner.py` 保持通过（现有 28 个测试继续 green）
3. ✅ 引擎不再对 `harness/runner.py` 生成重复 proposal（需修复 `_scan_code_structure()`）

### 验收方式
- 运行 `python -m pytest tests/test_harness_runner.py` 退出码 0（现有测试不受影响）
- 在 `zsiga/intake/evolution.py` 的 `_scan_code_structure()` 中验证 `harness/runner.py` 不再出现在 `modules_without_tests` 列表中

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（proposal 明确 out of scope）
- `tests/test_harness_runner.py`（现有测试文件，不在 proposal scope 内）

### 项目部署分支
deploy

### 已知风险
- **循环空转**：此 proposal 已被生成 27+ 次并全部 skip/reject，继续执行只是制造第 28 个冗余文件
- **basename 匹配 bug**：根因在 `zsiga/intake/evolution.py` L1090 的 `os.path.basename()` 逻辑，将 `harness/runner.py` 提取为 `runner`，但测试文件命名为 `test_harness_runner.py`（module 名 `harness_runner`），导致永远匹配失败
- **测试碎片化**：创建 `tests/test_runner.py` 会让同一模块拥有两个测试文件，增加维护负担

### 预估 token 消耗
- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考（此前同类 proposal 全部被 skip，无执行记录）
