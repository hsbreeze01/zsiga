# Clarify: fix-self-assessment-and-reflector-loop

## 需求拆解

### 原始需求
修复 self_assessment 记录缺失问题（当前仅 1 条），确保 REFLECT 阶段每次执行后都写入自评记录；同时为 Reflector 增加 auto-proposal 失败分析能力，避免同一 proposal 反复 VERIFY FAIL。

### 拆解后的子任务

- [ ] 1. **Self-assessment 写入修复** — 定位 `record_self_assessment()`（或等价函数）及其调用链，诊断为何 REFLECT 阶段未持久化自评记录，修复调用逻辑或 DB schema/异常处理，确保每次 REFLECT 执行后写入一条包含 change_name, outcome, reflection_text, lessons_learned, timestamp 的记录 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
  - 涉及文件：`zsiga/orchestrator.py`（REFLECT 阶段调度）、`zsiga/self_assessment.py`（或等价模块）、`zsiga/db.py`（schema）
  - 验证：模拟一次 REFLECT 阶段执行，断言 self_assessment 表新增记录

- [ ] 2. **Reflector stuck 检测与 proposal 抑制** — 在 reflector 中实现 `_is_stuck()` 逻辑，检查最近 3 次同 pattern auto-proposal 是否全部 VERIFY FAIL；若是则阻止重复生成，转而输出 `diagnosis.md`（包含失败列表、每次 FAIL 原因、人工介入建议），且该文件不触发 pipeline (预估复杂度：高, 预估 token：~6000 / 无历史参考)
  - 涉及文件：`zsiga/reflector.py`、`zsiga/db.py`（读取 phase_records）、`openspec/changes/` 目录写入
  - 验证：构造 3 次同名 VERIFY FAIL 历史 → 调用 reflector → 断言无新 proposal 但有 diagnosis.md 生成

- [ ] 3. **Reflector 历史感知 prompt 增强** — 修改 `generate_proposal()` 的 prompt/模板，注入该 pattern_key 最近 3 次 FAIL 原因，使新 proposal 能参考历史失败避免重复策略 (预估复杂度：中, 预估 token：~3500 / 无历史参考)
  - 涉及文件：`zsiga/reflector.py`（prompt 模板渲染逻辑）
  - 验证：含历史 FAIL 数据时，生成的 proposal prompt 中包含历史失败摘要

## 边界

### IN scope
- 修复 REFLECT 阶段 self_assessment 记录写入
- 实现 stuck 检测（连续 ≥3 次 VERIFY FAIL 同 pattern）并抑制重复 proposal
- 生成 `diagnosis.md` 作为人工介入入口（不触发 pipeline）
- 在 reflector proposal 生成 prompt 中注入历史失败上下文
- 更新或新增对应单元测试

### OUT of scope
- 修改 dashboard 前端展示 self_assessment 数据
- 修改 proposal 队列调度或 daemon 主循环逻辑
- 人工介入后的后续流程（仅生成 diagnosis.md）
- 跨 pattern 的失败分析或全局策略优化
- 修改 VERIFY 阶段本身的逻辑

### 依赖的外部条件
- `zsiga/orchestrator.py` 中 REFLECT 阶段入口可定位
- `zsiga/reflector.py` 中 `_is_duplicate()` 和 `generate_proposal()` 函数结构可扩展
- `zsiga/db.py`（或等价 DB 模块）中 changes 表的 phase_records 字段可查询
- 现有 `tests/test_self_assessment.py` 和 `tests/test_reflector.py` 可作为测试基线

## 目标

### 成功标准
1. REFLECT 阶段执行后，self_assessment 表新增一条完整记录（含 change_name, outcome, reflection_text, lessons_learned, timestamp）
2. 同一 auto-proposal pattern VERIFY FAIL ≥3 次后，reflector 不再生成该 pattern 的新 proposal
3. 被 stuck 检测拦截时，在 `openspec/changes/auto-stuck-{pattern_key}-{date}/` 下生成 `diagnosis.md`，包含失败列表、原因、建议
4. `diagnosis.md` 文件不触发 pipeline 执行
5. `generate_proposal()` 生成的 prompt 包含最近 3 次同 pattern FAIL 原因摘要
6. 全套 pytest 通过（含 `test_self_assessment.py`、`test_reflector.py` 及新增测试）

### 验收方式
- `pytest tests/test_self_assessment.py tests/test_reflector.py -v` 全绿
- 新增测试覆盖：stuck 检测（mock 3 次 FAIL → 断言无 proposal + 有 diagnosis.md）
- 新增测试覆盖：REFLECT 阶段调用后 self_assessment 写入
- 新增测试覆盖：prompt 注入历史失败上下文
- `ruff check` 无新增 lint 错误

## 约束

### 不能修改的文件
- `tests/conftest_zsiga.py`（共享 fixture，不改动）
- `site/dashboard.html`（前端不在 scope 内）
- `zsiga/__main__.py`（入口文件不改动）
- `pyproject.toml`、`requirements.txt`（不新增依赖）

### 项目部署分支
- `main`

### 已知风险
- self_assessment 的 DB schema 可能与预期不同，需运行时确认字段映射
- REFLECT 阶段可能存在异常被静默吞掉的情况，需排查 try/except 块
- stuck 检测需要高效的 pattern 匹配（proposal 命名规则可能不规范），需定义清晰的 pattern_key 提取逻辑
- `diagnosis.md` 写入 `openspec/changes/` 目录可能被 daemon 的 proposal 扫描器误识别，需确保文件名格式（`auto-stuck-*`）在扫描逻辑中被排除

### 预估 token 消耗
- prompt: ~18000
- completion: ~12000
- 数据来源: 无历史参考（首次涉及 self_assessment + reflector 联合修复）
