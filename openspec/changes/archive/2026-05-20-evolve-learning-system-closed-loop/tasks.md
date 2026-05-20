# Tasks

## 1. 结构化失败记录层（zsiga/memory/learn.py）

- [x] 1.1 扩展 `record_outcome()` 签名，增加 `error_domain`/`root_cause`/`prevention` 参数（默认 None）；重命名 `_classify_error` → `_classify_failure`，扩展为两层分类返回 dict（含 error_domain/root_cause_key/prevention），自动覆盖所有现有 lint 码 + test 细分 + pipeline 级；`record_outcome` 失败记录增加 error_domain/root_cause/prevention/what_happened 字段写入 learnings.jsonl
- [x] 1.2 新增 `record_success(change_name, project, phase_records, total_turns, total_seconds)` 函数，计算 first_pass 和 fix_attempts，写入 type="success_pattern" 记录到 learnings.jsonl
- [x] 1.3 新增 `tests/test_structured_failure.py` 覆盖 `_classify_failure` 两层分类、`record_outcome` 新参数向后兼容、lesson 新字段格式、`record_success` 记录格式

## 2. Pipeline 自诊断钩子（zsiga/pipeline/orchestrator.py）

- [ ] 2.1 在 `run_cycle()` 的 decompose 后置逻辑中增加 change_dir 存在性验证：对每个 subtask 的 transport 执行 `test -d`，失败时调用 `record_outcome(error_domain="pipeline")` 并降级为单项目
- [ ] 2.2 在 `_process_change()` 的 proposal 读取和 intent classify 后增加诊断记录：空 proposal 记录 `pipeline.proposal.empty`；`ask_user` 路由记录 `pipeline.intent.misclassify`；在 `_run_phases()` 交付成功后调用 `record_success()` 传入 phase_records 统计
- [ ] 2.3 新增 `tests/test_pipeline_hooks.py` 覆盖 decompose 降级、空 proposal 记录、intent misclassify 记录、成功后 record_success 调用

## 3. Skill 结晶器增强（skills/skill_evolver.py + zsiga/memory/pattern_miner.py）

- [ ] 3.1 修改 `Pattern` dataclass 增加 `all_preventions`/`all_root_causes`/`all_examples` 字段；修改 `mine_patterns()` 从 lesson 记录中提取并填充这些新字段
- [ ] 3.2 重写 `_generate_skill_markdown()` 生成 When to Apply / Rules（来自 prevention，回退 takeaway）/ Anti-Patterns（来自 root_cause）/ Examples（来自 context）四个新 section，保留原有 Patterns Observed 表格
- [ ] 3.3 修改 `evolve_skills()` 增加触发条件：`error_domain="pipeline"` 且 severity=high 立即触发；同 error_domain >= 2 次触发；新增 `_verify_skill_effectiveness()` 检查 root_cause 复发并标记 `verified` frontmatter
- [ ] 3.4 更新 `tests/test_skill_evolver.py` 覆盖新 section 生成、prevention→Rules 回退逻辑、pipeline 故障立即触发、有效性验证标记

## 4. 闭环注入与迁移（zsiga/memory/context.py + scripts/）

- [ ] 4.1 修改 `update_active_context()` 读取 skills/ 目录下最新 skill 文件的 Rules 部分，注入到 active_context.md 的 `## Active Skills` section
- [ ] 4.2 新增 `scripts/migrate_pattern_keys.py` 一次性迁移脚本：读取 learnings.jsonl，按映射表将旧 pattern_key 转换为新格式，补充 error_domain/root_cause/prevention 字段，写回文件（幂等）
- [ ] 4.3 运行全量测试确认所有改动通过（pytest + ruff check）
