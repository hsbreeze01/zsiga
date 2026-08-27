# clarify.md — add-tests-runner

> **⚠️ 前提校正**：proposal 声称 `zsiga/harness/runner.py` 缺少测试文件，这是**虚假前提**。
> `tests/test_harness_runner.py` 已存在（277 行，28 个 test 函数），覆盖全部 10 个公开类。
> 根因是 `evolution.py` 中 `_scan_code_structure()` 的 basename 匹配逻辑 bug，
> 导致引擎反复生成同名 proposal（27+ 次，全部 skip/reject）。
> 本 clarify 的实际目标是**修复引擎的测试发现逻辑**，而非创建冗余的 `test_runner.py`。

## 需求拆解

### 原始需求
为 `zsiga/harness/runner.py` 添加单元测试覆盖，创建 `tests/test_runner.py`。

### 真实需求
修复 `zsiga/intake/evolution.py` 中 `_scan_code_structure()` 的测试文件匹配逻辑，
使其能识别 `test_harness_runner.py` 覆盖了 `harness/runner.py`，从而消除 27+ 次空转循环。

### 拆解后的子任务

- [ ] 1. **修复 `_scan_code_structure()` 的 basename 匹配逻辑** (预估复杂度：中, 预估 token：~4000)
  - 文件：`zsiga/intake/evolution.py`（~L1068-1095）
  - 当前逻辑：`test_module = f.replace("test_", "").replace(".py", "")` → 精确匹配 basename
  - 修复为：增加后缀匹配 `test_module.endswith("_" + basename)` 或路径片段包含匹配
  - 使得 `"harness_runner".endswith("_runner")` → True，正确识别已有测试覆盖

- [ ] 2. **添加 proposal 去重黑名单机制** (预估复杂度：低, 预估 token：~2000)
  - 文件：`zsiga/intake/evolution.py`（proposal 生成函数附近）
  - 在 `_render_explore_proposal()` / `_render_test_proposal()` 中增加黑名单过滤
  - 将已知误报模式（如 `add-tests-runner`）加入硬编码黑名单，防止空转

- [ ] 3. **为修复逻辑添加回归测试** (预估复杂度：中, 预估 token：~3000)
  - 文件：`tests/test_evolution_proposal_quality.py`（已有 `_scan_code_structure` 相关测试）
  - 测试场景：当测试文件命名为 `test_{parent}_{module}.py` 时，`_scan_code_structure()` 能正确识别覆盖
  - 测试场景：黑名单机制能过滤已知的虚假 proposal 标题

## 边界

### IN scope
- 修改 `zsiga/intake/evolution.py` 中的 `_scan_code_structure()` 匹配逻辑
- 添加 proposal 标题黑名单过滤机制
- 在 `tests/test_evolution_proposal_quality.py` 中添加回归测试
- 验证 `add-tests-runner` proposal 不再被误生成

### OUT of scope
- ❌ 创建 `tests/test_runner.py`（已有 `tests/test_harness_runner.py` 覆盖）
- ❌ 修改 `zsiga/harness/runner.py` 源码
- ❌ 修改 `tests/test_harness_runner.py`
- ❌ 重构 evolution engine 的整体架构

### 依赖的外部条件
- `tests/` 目录中已存在 `test_harness_runner.py` 和 `test_evolution_proposal_quality.py`
- `zsiga/intake/evolution.py` 可正常导入（无 breaking changes）

## 目标

### 成功标准
1. `_scan_code_structure()` 能通过后缀匹配识别 `test_harness_runner.py` 覆盖了 `harness/runner.py`
2. `add-tests-runner` 不再出现在 `modules_without_tests` 结果中
3. proposal 黑名单机制生效，即使匹配逻辑遗漏，已知误报也不会生成 proposal
4. 新增回归测试全部通过（`python -m pytest tests/test_evolution_proposal_quality.py` 退出码 0）
5. 全量测试不引入回归（`python -m pytest` 退出码 0）

### 验收方式
- 运行 `python -m pytest tests/test_evolution_proposal_quality.py -v` 确认新增测试通过
- 运行 `python -m pytest tests/ -x` 确认无回归
- ruff check `zsiga/intake/evolution.py` 无新增 lint 问题

## 约束

### 不能修改的文件
- `zsiga/harness/runner.py`（proposal 明确 out of scope）
- `tests/test_harness_runner.py`（已有完善覆盖，无需改动）
- `pyproject.toml`、`requirements.txt`（不引入新依赖）

### 项目部署分支
- `zsiga` 项目的 deploy branch（由 `zsiga.yaml` 中 targets 配置决定）

### 已知风险
- **匹配逻辑过度宽松**：后缀匹配如果写得过于宽泛（如只检查 `endswith(basename)`），可能误判其他模块为已覆盖。需要精确到 `_` 分隔的片段匹配
- **黑名单维护成本**：硬编码黑名单是防御措施，长期应靠匹配逻辑修复根本解决。黑名单应保持最小
- **`_scan_code_structure` 现有测试**：`tests/test_evolution_proposal_quality.py` 已有 3 个相关测试（L144, L164, L181），修改逻辑后需确认这些测试仍通过

### 预估 token 消耗
- prompt: ~8000（阅读 evolution.py 相关代码 + 现有测试 + 生成修复）
- completion: ~4000（修改代码 + 添加测试）
- 数据来源: 无历史参考（首次修复此类引擎 bug）
