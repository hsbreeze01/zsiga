# Proposal: Implement Real CLARIFY Phase + OPTIMIZE Phase

## Summary

之前 `clarify-requirement-engineering` 和 `optimize-norm-alignment` 两个 proposal 被 zsiga 处理后，实际只做了表面改动：
- CLARIFY 只是把 enrich 阶段的结果标记为 `Phase.CLARIFY`，并不是独立的阶段
- OPTIMIZE 完全没有实现（枚举里不存在）

需要真正实现这两个阶段。

## Current State

```
CLARIFY(=enrich改名) → IMPLEMENT → REVIEW → VERIFY → REFLECT → DELIVER
```

Phase 枚举：`CLARIFY, IMPLEMENT, REVIEW, VERIFY, REFLECT, DELIVER`（缺少 OPTIMIZE）

## Target State

```
CLARIFY(独立) → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE(可选) → REFLECT → DELIVER
```

Phase 枚举：`CLARIFY, ENRICH, IMPLEMENT, REVIEW, VERIFY, OPTIMIZE, REFLECT, DELIVER`

## Requirements

### 1. 恢复 ENRICH 阶段
- 文件：`zsiga/pipeline/orchestrator.py`
- 当前 CLARIFY 标记在 enrich 调用上（第 390 行 `phase=Phase.CLARIFY`），改回 `phase=Phase.ENRICH`
- Phase 枚举中加回 `ENRICH = "enrich"`

### 2. 实现真正的 CLARIFY 阶段（enrich 之前）
- 位置：在 enrich 之前，作为一个独立 phase
- 功能：**需求澄清**——读取 proposal.md，输出结构化需求契约到 `{change_dir}/clarify.md`
  - 需求拆解：将模糊需求拆为可验证的子需求
  - 边界定义：明确什么在 scope 内/外
  - 目标对齐：与项目既有架构对齐
  - 约束梳理：技术约束、安全约束、性能约束
- 使用主 agent（不是子代理），给 1-2 轮即可（轻量）
- 输出 `clarify.md` 后，enrich 阶段可以引用它来减少探索量

### 3. 实现 OPTIMIZE 阶段（verify 之后，可选）
- 文件：`zsiga/pipeline/orchestrator.py`、`zsiga/metrics/types.py`
- Phase 枚举新增 `OPTIMIZE = "optimize"`
- 位置：VERIFY 通过后、REFLECT 之前
- 触发条件：可选（默认启用，可通过 config 关闭）
- 功能：**优化迭代**
  - 规范对齐：检查代码是否符合项目既有风格/规范
  - 冗余剔除：删除死代码、未使用的 import
  - 可读性提升：改善命名、添加必要注释
  - 性能优化：识别明显的性能问题
- 使用主 agent，给 3-5 轮，限制只改本次变更涉及的文件
- 配置项：`zsiga.yaml` 的 pipeline 段加 `optimize_enabled: true`

### 4. 修复 Phase 枚举
- 文件：`zsiga/metrics/types.py`
- 最终枚举：`CLARIFY, ENRICH, IMPLEMENT, REVIEW, VERIFY, OPTIMIZE, REFLECT, DELIVER`

### 5. Dashboard Phase Performance 表格
- 确保 CLARIFY、ENRICH、OPTIMIZE 三个新阶段在 dashboard 的 Phase Performance 表中出现
- `_phase_table` 已自动展示所有有数据的 phase，无需额外修改

## Constraints
- Scope: project=zsiga
- 关键文件：`zsiga/metrics/types.py`（枚举）、`zsiga/pipeline/orchestrator.py`（pipeline 流程）、`zsiga.yaml`（配置）
- 不要改动已有阶段的逻辑（IMPLEMENT/REVIEW/VERIFY/REFLECT/DELIVER 保持不变）
- 运行 pytest 确认不破坏现有测试
