# clarify.md — add-tests-runner

> **⚠️ 关键发现：此 proposal 的核心前提已被证实为虚假。**
> `tests/test_harness_runner.py`（277 行，28 个 `def test_` 函数，5 个测试类）已全面覆盖 `zsiga/harness/runner.py` 的全部 10 个类。此 proposal 是自演进引擎 basename 匹配 bug 的产物，已被生成 27+ 次并全部被 skip/reject。

## 需求拆解

### 原始需求

Proposal 要求为 `zsiga/harness/runner.py`（352 行，10 个类）创建测试文件 `tests/test_runner.py`，声称该模块缺少测试覆盖。

**事实核查**：`tests/test_harness_runner.py` 已存在，包含：

| 测试类 | 覆盖范围 |
|---|---|
| `TestEventDataclasses` | `TestStarted`, `TestPassed`, `TestFailed`, `TestError` |
| `TestHarnessResult` | `HarnessResult` 默认值、自定义值 |
| `TestHarnessRunnerDiscover` | `discover()` 正常/空目录/不存在目录 |
| `TestHarnessRunnerRun` | `run()` 通过/失败/异常/多文件/timestamp |
| `TestHarnessRunnerPytestFailClosed` | `run_pytest()` 空文件/语法错误/报告结构 |

**根因**：`zsiga/intake/evolution.py:1093-1102` 的 `_scan_code_structure()` 用 basename 提取模块名 `runner`，但已有测试文件名提取为 `harness_runner`，二者不匹配 → 引擎反复认为"无测试"。

### 拆解后的子任务

- [ ] 1. 修复 `_scan_code_structure()` 的测试文件发现逻辑 — 将 basename 精确匹配改为子串/路径感知匹配，使 `test_harness_runner.py` 能被关联到 `harness/runner.py`（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 2. 为 evolution engine 添加 proposal 去重/黑名单机制 — 对连续 N 次 skip/reject 的 proposal 模式自动抑制，避免无限循环空转（预估复杂度：高, 预估 token：~6000 / 无历史参考）
- [ ] 3. 验证修复后引擎不再生成 `add-tests-runner` 类虚假 proposal — 运行 `_scan_code_structure()` 确认 `runner.py` 被正确识别为已有测试覆盖（预估复杂度：低, 预估 token：~1500 / 无历史参考）

## 边界

### IN scope
- 修复 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的测试文件发现逻辑
- 添加 proposal 模式去重/黑名单机制（可选，视精力）
- 验证修复效果

### OUT of scope
- ❌ 创建 `tests/test_runner.py`（与已有 `test_harness_runner.py` 完全冗余）
- ❌ 修改 `zsiga/harness/runner.py` 源码
- ❌ 修改 `tests/test_harness_runner.py` 已有测试

### 依赖的外部条件
- `_scan_code_structure()` 方法在 `zsiga/intake/evolution.py:1068` 附近，需理解其调用链
- 现有测试 `tests/test_harness_runner.py` 不受影响
- 需要确认修改后 `evolution.py` 不破坏其他模块（如 `add-tests-config` 等）的测试发现

## 目标

### 成功标准
1. `_scan_code_structure()` 能正确将 `tests/test_harness_runner.py` 关联到 `zsiga/harness/runner.py`（即 `runner` 模块被识别为已有测试覆盖）
2. 引擎不再为已有测试覆盖的模块生成 `add-tests-*` proposal
3. 所有现有测试（`python -m pytest`）通过，包括 `tests/test_harness_runner.py`

### 验收方式
- 在 `_scan_code_structure()` 中打印/断言 `runner` 模块的测试文件发现结果，确认包含 `test_harness_runner`
- 运行完整测试套件确认无回归
- （可选）模拟运行 evolution cycle 确认不再生成 `add-tests-runner`

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py` — 源码不可修改
- `tests/test_harness_runner.py` — 已有测试不可修改
- `site/dashboard.html` — 前端无关

### 项目部署分支
- deploy

### 已知风险
- **历史循环风险**：此 proposal 模式已空转 27+ 次，如果本次只处理 proposal 原文需求（创建冗余 test_runner.py），将在下一次 evolution cycle 再次生成相同 proposal，形成无限循环
- **basename 匹配修复范围**：修改 `_scan_code_structure()` 可能影响其他模块的测试发现（如 `config.py` vs `test_config_*.py`），需确认无回归
- **proposal 去重机制的边界**：黑名单过于激进可能抑制合理的 proposal

### 预估 token 消耗
- prompt: ~5000
- completion: ~3000
- 数据来源: 无历史参考（首次处理引擎级 bug 而非业务代码变更）
