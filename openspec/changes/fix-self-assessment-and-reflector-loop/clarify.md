# Clarify: fix-self-assessment-and-reflector-loop

## 需求拆解

### 原始需求
修复 self_assessment 记录缺失（仅 1 条），确保 REFLECT 阶段每次执行后写入自评记录；同时为 Reflector 增加 auto-proposal 失败分析能力，避免同一 proposal 反复 VERIFY FAIL。

### 拆解后的子任务

- [ ] 1. **Self-assessment 写入修复** — 排查 `record_self_assessment()` 调用链，确认 REFLECT 阶段是否调用、DB schema 是否匹配、异常是否被吞掉，修复后确保每次 REFLECT 执行都写入一条完整记录（change_name, outcome, reflection_text, lessons_learned, timestamp）(预估复杂度：中, 预估 token：~8000 / 无历史参考)
- [ ] 2. **Reflector auto-proposal 卡死检测** — 在 `reflector.py` 新增 `_is_stuck()` 方法，检查最近 3 次同名/同 pattern 的 auto-proposal 是否全部 VERIFY FAIL，若是则拦截并生成 `diagnosis.md`（含失败 proposal 列表、每次 FAIL 原因、人工介入建议），不再重复生成该 proposal (预估复杂度：中, 预估 token：~10000 / 无历史参考)
- [ ] 3. **Reflector 历史感知增强** — 修改 `generate_proposal()` 的 prompt/模板，在渲染 proposal 时注入该 pattern_key 最近 3 次的 FAIL 原因，让 LLM 参考历史失败避免重复相同策略 (预估复杂度：低, 预估 token：~5000 / 无历史参考)
- [ ] 4. **测试覆盖** — 为上述三个功能模块编写/补充 pytest：REFLECT 后 self_assessment 新增记录、stuck 检测拦截并生成 diagnosis.md、历史注入到 proposal prompt (预估复杂度：中, 预估 token：~6000 / 无历史参考)

## 边界

### IN scope
- 修复 self_assessment 在 REFLECT 阶段的写入逻辑
- 新增 `_is_stuck()` 卡死检测与 `diagnosis.md` 生成
- 增强 `generate_proposal()` 的历史失败注入
- 相关 pytest 测试用例

### OUT of scope
- 重构 orchestrator 整体架构
- 修改 DB schema（除非当前 schema 不匹配导致写入失败）
- Dashboard 展示 self_assessment 数据
- 非 auto-proposal 的人工 proposal 流程变更

### 依赖的外部条件
- `reflector.py` 和 `orchestrator.py` 的 REFLECT 阶段代码可读可改
- `self_assessment` 表的 DB schema 定义可查
- `changes` 表的 `phase_records` 可读（用于提取 FAIL 原因）

## 目标

### 成功标准
1. REFLECT 阶段执行后，`self_assessment` 表新增一条包含 change_name、outcome、reflection_text、lessons_learned、timestamp 的记录
2. 同一 auto-proposal pattern VERIFY FAIL >= 3 次后，`_is_stuck()` 返回 True，Reflector 不再重复生成该 proposal
3. 被 `_is_stuck()` 拦截时，在 `openspec/changes/auto-stuck-{pattern_key}-{date}/` 下生成 `diagnosis.md`（含失败列表、原因、人工介入建议），不触发 pipeline
4. `generate_proposal()` 渲染时注入最近 3 次 FAIL 原因到 prompt
5. 全套 `tests/test_self_assessment.py` 和 `tests/test_reflector.py` 通过

### 验收方式
- 手动/CI 运行 `pytest tests/test_self_assessment.py tests/test_reflector.py -v` 全部通过
- 检查 REFLECT 执行后 DB 中 `self_assessment` 表有新记录
- 模拟 3 次 VERIFY FAIL 后确认不再生成重复 proposal、确认生成 diagnosis.md

## 约束

### 不能修改的文件
- `venv2/` 下所有文件
- `pyproject.toml`、`requirements.txt`
- `site/dashboard.html`（本次不涉及前端）
- `tests/conftest_zsiga.py`（除非必要且不影响其他测试）

### 项目部署分支
- main

### 已知风险
- `record_self_assessment()` 可能根本不存在，需要从 REFLECT 阶段逻辑中定位等价写入点
- DB 写入可能因异常被静默吞掉（broad except），需排查 try/except 块
- `phase_records` 中 FAIL 原因的提取格式可能不统一，需要做防御性解析
- Reflector 的 proposal 生成可能依赖 LLM，历史注入的 prompt 长度需控制在 token budget 内

### 预估 token 消耗
- prompt: ~15000
- completion: ~12000
- 数据来源: 无历史参考
