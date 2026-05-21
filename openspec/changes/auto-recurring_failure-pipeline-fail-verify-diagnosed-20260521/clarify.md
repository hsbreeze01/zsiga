# Clarify: Fix Recurring `pipeline.fail.verify.diagnosed` Pattern

## 需求拆解

### 原始需求
修复反复出现的 `pipeline.fail.verify.diagnosed` 失败模式（已观测 3 次）。所有诊断结论均为"未确认假设"，表明验证阶段的诊断逻辑过于笼统，无法定位真实根因，导致同一类失败反复发生。

### 拆解后的子任务
- [ ] 1. **分析 verify + diagnose 流程，定位模糊诊断的根源** — 阅读管道 verify 阶段和 diagnoser 模块的代码，找出为什么所有诊断结论都是 "Unconfirmed hypothesis" 以及根因分类过于宽泛的原因。输出：明确代码瓶颈位置和改进方案。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 2. **增强诊断器：细化根因分类与确定性判定** — 改进 diagnoser 使其能根据实际错误信息（lint 错误、import 缺失、assert 失败等）生成具体根因和可执行的修复建议，不再输出 "Unconfirmed hypothesis" 这类无帮助信息。涉及文件：`zsiga/pipeline/diagnoser.py`（或等效模块）。（预估复杂度：高, 预估 token：~6000 / 无历史参考）
- [ ] 3. **在 verify 阶段增加预校验（import/依赖/lint 快检）** — 在正式 verify 之前增加轻量级预检，提前捕获 "Missing or incorrect import / dependency" 和 lint 错误，避免进入诊断流程。涉及文件：`zsiga/pipeline/` 下 verify 相关模块。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 4. **补充测试：覆盖改进后的诊断与预校验逻辑** — 为 diagnoser 的新根因分类和 verify 预校验添加单元测试，确保不再退化到 "Unconfirmed hypothesis" 输出。涉及文件：`tests/test_diagnoser.py`、`tests/test_recovery.py` 等。（预估复杂度：中, 预估 token：~3000 / 无历史参考）

## 边界

### IN scope
- 改进 diagnoser 的根因分类精度和修复建议具体性
- 在 verify 阶段增加预校验（import/依赖/lint 快检）以提前拦截已知失败模式
- 为改进逻辑补充对应的单元测试
- 确保所有改动通过 `pytest` 和 `ruff`

### OUT of scope
- 不改动管道的其他阶段（implement、review、deliver）
- 不改动 dashboard 或前端
- 不改动 daemon 调度逻辑
- 不改动 `memory/learnings.jsonl` 的采集方式

### 依赖的外部条件
- `zsiga/pipeline/` 目录下的 verify 和 diagnose 模块存在且可修改
- 现有测试框架（pytest）可正常运行
- 项目 Python 环境可用

## 目标

### 成功标准
1. diagnoser 在遇到 import 错误、lint 错误、assert 失败时，输出具体根因（不再出现 "Unconfirmed hypothesis"）
2. verify 阶段在正式执行前能拦截至少 "Missing import" 和 "lint error" 两类已知失败模式
3. 新增测试全部通过，覆盖诊断器的主要根因分类路径
4. 现有测试不被破坏（`pytest` 全绿）
5. 代码通过 `ruff check`

### 验收方式
- 运行 `pytest tests/test_diagnoser.py tests/test_recovery.py -v` 全部通过
- 检查 diagnoser 对已知失败样本的输出，确认根因描述具体且可操作
- 运行 `ruff check` 无报错

## 约束

### 不能修改的文件
- `site/dashboard.html`
- `venv2/` 下所有文件
- `memory/learnings.jsonl`
- `data/zsiga.db`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
`main`

### 已知风险
- `zsiga/pipeline/` 的具体文件结构未在上下文中完整展示，实施时需先确认模块位置
- diagnoser 可能被多个阶段调用，改动需注意不影响其他流程
- 预校验可能增加 verify 阶段耗时，需保持轻量

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考
