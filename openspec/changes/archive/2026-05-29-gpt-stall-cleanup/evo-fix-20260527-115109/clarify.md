# clarify.md — diagnose-recent-failures

## 需求拆解

### 原始需求
诊断最近 24 小时内 10 次未解决的 pipeline 失败（均为 STEWARD REJECT），分析根因模式，对可修复问题实施针对性修复，对不可修复问题记录 learning 并标记 capability boundary。

### 拆解后的子任务

- [ ] 1. **收集与分析失败案例** — 读取 `openspec/changes/` 下失败变更的 `diagnosis.md`、`verify.md`、`steward-review-*.md`，提取每个失败的根因、阶段、score。输出结构化的根因分析报告写入本 change 目录。（预估复杂度：中, 预估 token：~4000）
- [ ] 2. **共性根因提取与分类** — 从任务 1 的分析结果中归纳共性模式（如：自指循环、AC 空洞、静态分析数据失真、目标模块已有测试等），将根因分为「可修复」和「capability boundary」两类。（预估复杂度：低, 预估 token：~2000）
- [ ] 3. **可修复根因的针对性修复** — 针对任务 2 中标记为「可修复」的根因，修改对应的源码文件并编写/更新测试。每个修复必须通过 `ruff check` 和 `pytest`。（预估复杂度：高, 预估 token：~8000）
- [ ] 4. **记录 learnings 与 capability boundary 标记** — 将不可修复的根因（如自演进引擎的静态分析局限、模板化 proposal 的 AC 质量问题）写入 `memory/learnings.jsonl`，标记为 capability boundary，防止后续重复生成同类 proposal。（预估复杂度：低, 预估 token：~2000）

## 边界

### IN scope
- 分析 `openspec/changes/` 下最近 24h 内 STEWARD REJECT 的失败案例
- 读取各失败案例的 diagnosis.md / verify.md / steward-review 文件
- 提取共性根因模式并分类
- 对可修复的根因实施源码级修复（含测试）
- 对不可修复的根因写入 learning 记录

### OUT of scope
- 修改 `zsiga/intake/evolution.py` 的 proposal 生成模板（属于更大的架构变更）
- 修改 proposal_gate / steward 评分逻辑
- 修改 daemon 主循环
- 重新运行已被 reject 的历史 proposal

### 依赖的外部条件
- `openspec/changes/` 目录下失败案例的 diagnosis.md / verify.md / steward-review 文件必须存在且可读
- `memory/learnings.jsonl` 可写入
- 项目测试环境可用（pytest + ruff）

## 目标

### 成功标准
1. 完成至少 2 个失败案例的根因分析，产出结构化报告
2. 若存在可修复根因，修复后对应模块的测试全部通过（pytest exit 0）
3. 若存在不可修复根因，至少 1 条 learning 记录写入 `memory/learnings.jsonl`，包含 `pattern_key`、`root_cause`、`prevention` 字段
4. 所有变更通过 `ruff check` 无报错

### 验收方式
- 检查本 change 目录下是否存在根因分析报告文件
- `pytest` 相关测试全部通过
- `ruff check` 无报错
- `memory/learnings.jsonl` 中包含本次新增的 learning 条目（grep 验证）

## 约束

### 不能修改的文件
- `zsiga/intake/evolution.py`（proposal 生成模板不在本次 scope 内）
- `zsiga/daemon.py`（主循环不改动）
- `tests/conftest_zsiga.py`（共享 fixture 不改动）
- `pyproject.toml`、`requirements.txt`（依赖不改动）

### 项目部署分支
main

### 已知风险
- **自指循环风险**：`diagnose-recent-failures` 类 proposal 历史上已被 STEWARD 反复拒绝（20+ 次），拒绝理由均为"自指循环"。本次执行若只产出分析报告而不实施具体修复，可能被判定为无实质进展
- **失败案例数据不完整**：部分历史失败案例可能已被 archive 或 cleanup，diagnosis.md / verify.md 可能缺失
- **可修复根因数量不确定**：10 次 STEWARD REJECT 的根因可能是 proposal 质量问题（AC 空洞、前提错误），这类问题需要修改 evolution.py 模板才能真正修复，而该文件在 OUT of scope 中
- **capability boundary 记录可能不足**：如果所有根因都被归类为"需要架构级改动"，则实际可执行的修复量为零

### 预估 token 消耗
- prompt: ~12000
- completion: ~6000
- 数据来源: 无历史参考（同类 proposal 从未被成功实施）
