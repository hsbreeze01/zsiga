# clarify.md — add-tests-runner

## 需求拆解

### 原始需求
proposal 声称为 `zsiga/harness/runner.py`（352 行，10 个类）添加单元测试，新建 `tests/test_runner.py`。

### 事实核查

**核心前提不成立：测试已存在。**

`tests/test_harness_runner.py`（277 行，20+ 个 `def test_` 函数）已全面覆盖 `zsiga/harness/runner.py` 的所有公开 API：

| 已有测试类 | 测试数 | 覆盖目标 |
|---|---|---|
| `TestEventDataclasses` | 4 | TestStarted / TestPassed / TestFailed / TestError |
| `TestHarnessResult` | 2 | HarnessResult 默认值 / 自定义值 |
| `TestHarnessRunnerDiscover` | 3 | discover() 正常 / 空目录 / 不存在目录 |
| `TestHarnessRunnerRun` | 7 | run() pass / fail / error / 多文件 / 无 discovery / 时间戳 |
| `TestHarnessRunnerPytestFailClosed` | 4 | run_pytest() 空文件 / 语法错误 / QualificationReport / TestReport |

### 拆解后的子任务

- [ ] 1. **拒绝此 proposal** — 测试已存在，无需新建（预估复杂度：低，预估 token：~200 / 无历史参考）
- [ ] 2. **（引擎修复）修正 `_scan_code_structure()` 的测试文件发现逻辑** — 在 `zsiga/intake/evolution.py` 中，将 basename 匹配改为考虑完整路径模式（`test_{parent}_{basename}.py`），根除此空转循环（预估复杂度：中，预估 token：~2000 / 无历史参考）

## 边界

### IN scope
- 识别并记录 proposal 前提错误的事实
- 指出引擎静态分析的 bug（basename 匹配逻辑）

### OUT of scope
- 创建 `tests/test_runner.py`（与 `tests/test_harness_runner.py` 完全重复）
- 修改 `zsiga/harness/runner.py` 源码
- 修改引擎代码（属于另一个 proposal 的 scope）

### 依赖的外部条件
- `tests/test_harness_runner.py` 持续存在且 pytest 通过

## 目标

### 成功标准
1. 不创建冗余测试文件 `tests/test_runner.py`
2. 引擎不再为 `harness/runner.py` 生成 `add-tests-runner` proposal
3. 此空转循环的第 27+ 次重复被终止

### 验收方式
- `tests/test_runner.py` **不存在**（验证未产生冗余文件）
- `python -m pytest tests/test_harness_runner.py` 退出码 0（验证已有测试健康）
- 此 proposal 被 SKIP 或 REJECT

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`
- `tests/test_harness_runner.py`
- 任何源码文件

### 项目部署分支
- deploy

### 已知风险
- **空转循环**：同名 `add-tests-runner` proposal 已被生成 26+ 次，全部被 skip/reject，消耗了大量 token。根因是 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 使用 `os.path.basename(pf).replace(".py", "")` 提取 `runner`，但测试文件命名为 `test_harness_runner.py`，提取结果为 `harness_runner`，两者不匹配
- **引擎 bug 未修复**：即使此 proposal 被拒绝，引擎仍会在下一轮扫描中再次生成同名 proposal，除非 `_scan_code_structure()` 的匹配逻辑被修正

### 预估 token 消耗
- prompt: ~500
- completion: ~300
- 数据来源: 无历史参考（本 proposal 应直接终止，不进入实施阶段）
