# clarify.md — add-tests-runner

> **⚠️ 致命前提问题：本 proposal 基于虚假前提生成，不应执行。**
>
> 并行探索（5 个 Agent 一致确认）证实：`tests/test_harness_runner.py`（277 行，28 个 `def test_` 函数，6 个测试类）**已全面覆盖** `zsiga/harness/runner.py` 的全部 10 个类。本 proposal 是自演进引擎 basename 匹配 bug 导致的第 27+ 次循环空转产物。

---

## 需求拆解

### 原始需求
proposal 声称为 `zsiga/harness/runner.py`（352 行，10 个 dataclass 类，0 个独立函数）新建 `tests/test_runner.py`，覆盖公开 API。

**实际情况**：该模块已有完整测试覆盖，不需要新增测试文件。

### 拆解后的子任务

- [ ] 1. ~~新建 `tests/test_runner.py` 并编写测试~~ — **不需要执行**
  - 预估复杂度：N/A（冗余任务）
  - 理由：`tests/test_harness_runner.py` 已存在，包含 `TestEventDataclasses`、`TestHarnessResult`、`TestHarnessRunnerDiscover`、`TestHarnessRunnerRun`、`TestHarnessRunnerPytestFailClosed` 共 5 个测试类 28 个测试函数，覆盖全部公开 API
- [ ] 2. **修复根因：`zsiga/intake/evolution.py` 的 `_scan_code_structure()` basename 匹配逻辑** — **这才是真正需要的**
  - 预估复杂度：低
  - 预估 token：~1500
  - 当前逻辑：`test_module = f.replace("test_", "").replace(".py", "")` 提取出 `harness_runner`，然后与 `basename = os.path.basename(pf).replace(".py", "")` 提取出的 `runner` 做精确匹配 → 失败
  - 修复方案：改为子串包含匹配（`basename in test_module` 或 `test_module in basename`）或从 test 文件名中提取所有可能的 module 名片段

## 边界

### IN scope
- （本 proposal 原始 scope 全部无效，因前提虚假）
- **替代建议**：修复 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的测试文件发现逻辑，使其能正确识别 `test_harness_runner.py` 是 `runner.py` 的测试文件

### OUT of scope
- 新建 `tests/test_runner.py`（将与已有 `tests/test_harness_runner.py` 完全冗余重叠）
- 修改 `zsiga/harness/runner.py` 源码

### 依赖的外部条件
- 无（修复 basename 匹配逻辑不依赖外部条件）

## 目标

### 成功标准
1. ~~`tests/test_runner.py` 存在且 pytest 通过~~ — **标准无效，文件不应创建**
2. **替代标准**：`_scan_code_structure()` 能正确识别 `test_harness_runner.py` 覆盖了 `runner.py`，不再生成 `add-tests-runner` proposal
3. 已有测试 `tests/test_harness_runner.py` 保持 pytest 退出码 0

### 验收方式
- 确认 `python -m pytest tests/test_harness_runner.py` 退出码 0（验证已有测试未被破坏）
- 确认引擎在下一轮扫描中不再生成 `add-tests-runner` proposal（需观察一个完整演进窗口）
- 如果执行修复：`python -m pytest tests/` 全量通过

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（proposal 明确声明不修改源码）
- `tests/test_harness_runner.py`（已有完整测试，不应被覆盖或重命名）

### 项目部署分支
- deploy

### 已知风险
- **循环空转风险（已发生 27+ 次）**：如果只创建 `tests/test_runner.py` 而不修复 basename 匹配 bug，引擎在下一轮扫描中仍可能因为其他模块的类似命名问题产生新的冗余 proposal
- **根因未解**：`evolution.py` 的 basename 精确匹配逻辑不仅影响 `runner.py`，还可能影响所有测试文件名包含额外前缀/后缀的模块（如 `test_foo_bar.py` 覆盖 `bar.py`）
- **archive 污染**：已有 20+ 个 skipped archive 目录由同名 proposal 产生，占用磁盘空间但不影响运行时

### 预估 token 消耗
- **如果执行原始 proposal（创建冗余测试）**：prompt ~1200, completion ~800 — 浪费
- **如果修复根因 bug**：prompt ~800, completion ~400
- 数据来源: historical（27+ 轮循环消耗的历史数据）
