# Design: 闭环学习系统

## 架构决策

### 1. 两层错误分类而非三层

proposal 建议三层（故障域/根因/教训），但教训层的 `what_happened`/`root_cause`/`prevention`/`fix_applied` 实质是 lesson 记录的字段，不是分类层级。因此只做两层分类（domain + root_cause_key），教训信息作为 lesson 记录的字段存储。

**理由**：保持 pattern_key 格式简洁（`domain.root_cause`），与 pattern_miner 的分组逻辑兼容。

### 2. record_outcome 向后兼容扩展

通过为所有新参数添加默认值 `None`，保证现有调用点无需修改。当 `error_domain=None` 时，由 `_classify_failure()` 从 `detail` 参数自动推断。

**理由**：orchestrator.py 中有 5 个 `record_outcome()` 调用点，逐一修改风险大。默认值策略让新调用点可以传入结构化信息，旧调用点自动推断。

### 3. Pipeline 钩子不引入新的抽象层

不在 orchestrator 中引入 validator 中间件。每个验证点直接内联在 orchestrator 的流程中，调用 `record_outcome()` 并处理降级。

**理由**：orchestrator 已经是最复杂的文件（841行），引入新抽象增加认知复杂度。内联钩子更直观，且只影响局部代码段。

### 4. skill_evolver 增强而非重写

保留现有 `_cluster_patterns()`、`_derive_filename()`、`_is_auto_generated()`、`_prune_stale_skills()` 的逻辑。只修改 `_generate_skill_markdown()` 增加 When to Apply / Rules / Anti-Patterns / Examples 部分。

**理由**：现有测试（`test_skill_evolver.py`）覆盖了聚类、去重、幂等、手写保护、修剪等核心逻辑。增强方式让现有测试继续通过，只需新增测试覆盖新 section。

### 5. 成功记录复用 learnings.jsonl

不新建 `successes.jsonl`。成功和失败记录共享同一个文件，通过 `type` 字段区分。

**理由**：pattern_miner 已经统一处理 learnings.jsonl。分离存储意味着 pattern_miner 需要读两个文件。共享存储简化数据流。

## 数据流

```
Change 完成（成功或失败）
    │
    ├─ 失败 → record_outcome(error_domain, root_cause, prevention)
    │          → _classify_failure(detail) 自动推断
    │          → learnings.jsonl: {type:"lesson", error_domain, root_cause, prevention, ...}
    │
    └─ 成功 → record_success(change_name, project, phase_records, ...)
              → learnings.jsonl: {type:"success_pattern", first_pass, total_turns, ...}
    │
    ▼
_update_memory()
    │
    ├─ pattern_miner.mine_patterns() → 按 pattern_key 聚类
    │
    ├─ skill_evolver.evolve_skills()
    │   │
    │   ├─ 读取 learnings.jsonl 中每条记录的 prevention/root_cause/what_happened
    │   ├─ 按 cluster 生成 skill 文件（含 When to Apply / Rules / Anti-Patterns / Examples）
    │   └─ 验证 skill 有效性（检查 root_cause 是否复发）
    │
    └─ context.py update_active_context()
        → 注入 skill 规则到 active_context.md
```

## 文件变更列表

### 新增文件
| 文件 | 说明 |
|------|------|
| `scripts/migrate_pattern_keys.py` | 一次性迁移脚本：旧 pattern_key → 新格式 |

### 修改文件
| 文件 | 变更说明 |
|------|----------|
| `zsiga/memory/learn.py` | 扩展 `record_outcome()` 签名；重命名 `_classify_error` → `_classify_failure` 并扩展分类；新增 `record_success()`；lesson 记录增加 `error_domain`/`root_cause`/`prevention` 字段 |
| `zsiga/pipeline/orchestrator.py` | 在 `run_cycle()` 中增加 decompose 后置验证；在 `_process_change()` 中增加 proposal 空内容记录和 intent misclassify 记录；在 `_run_phases()` 交付成功后调用 `record_success()`；在 `_update_memory()` 中调用 `evolve_skills()` 并注入 skill 规则 |
| `skills/skill_evolver.py` | 修改 `_generate_skill_markdown()` 增加 When to Apply / Rules / Anti-Patterns / Examples 部分；修改 `evolve_skills()` 增加基于 error_domain 和 severity 的触发条件；新增 skill 有效性验证逻辑 |
| `zsiga/memory/context.py` | 修改 `update_active_context()` 注入最新 skill 规则到 active_context.md |
| `zsiga/memory/pattern_miner.py` | 修改 `mine_patterns()` 读取 lesson 记录的新字段（prevention/root_cause/error_domain），传递给 Pattern 数据结构 |

### 新增测试文件
| 文件 | 说明 |
|------|------|
| `tests/test_structured_failure.py` | 测试 `_classify_failure()` 两层分类、`record_outcome()` 新参数、lesson 新字段 |
| `tests/test_success_recording.py` | 测试 `record_success()` 的记录格式和 learnings.jsonl 写入 |
| `tests/test_pipeline_hooks.py` | 测试 decompose 验证、proposal 空内容处理、intent misclassify 记录 |
| `tests/test_skill_crystallizer.py` | 测试增强的 skill 生成格式、结晶触发条件、有效性验证 |

### 修改测试文件
| 文件 | 变更说明 |
|------|----------|
| `tests/test_pattern_miner.py` | 更新测试以覆盖新字段（prevention/root_cause）的传播 |
| `tests/test_skill_evolver.py` | 更新 `_generate_skill_markdown` 测试以验证新 section（When to Apply / Rules / Anti-Patterns / Examples） |
