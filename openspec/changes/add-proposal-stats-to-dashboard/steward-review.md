## Verdict: PUSHBACK

## 我的判断

这个 proposal 的方向是对的——给 dashboard 加 proposal 统计是合理的运维需求。但它有一个致命的设计错误：**它假设数据存在 SQLite 表里，而实际数据是 `~/.openspec/changes/*.json` 文件。** 整个 Technical Design 里的四条 SQL 查询全部是废话，实现路径根本行不通。我无法放行一个核心技术假设就错误的方案，哪怕方向正确。

## 评分详情
- **可行性: 1/2** — `zsiga/daemon.py` 存在，`_serve_dashboard` 路由模式存在，`_build_status_json` 等函数可参考。但核心假设错了：代码库里没有 `changes` SQLite 表，数据源是 `Path(home) / "openspec" / "changes"` 下的 JSON 文件（确定性事实已验证 `sqlite3` 符号未找到定义）。实现需要全部重写数据访问逻辑。
- **可执行性: 1/2** — 给了具体的函数签名、SQL 语句、路由路径，看起来很详细。但四条 SQL（`SELECT COUNT(*) FROM changes` 等）全部指向一个不存在的表——这条路径实际不可执行。需要改为 Python 内存聚合 JSON 文件。
- **能力匹配: 1/2** — 无此类任务的成功记录。
- **历史风险: 1/2** — `dashboard-add-feedback-loop-metrics` 在 implement 和 verify 阶段连续失败 4 次（2026-05-21 至 05-23），失败模式是"test expectations don't match implementation"。同类 dashboard 指标扩展任务有明确的失败史。
- **范围合理性: 2/2** — 单文件、只读、无状态变更、不影响现有端点。边界清晰。
- **总分: 6/10**

## 疑虑
1. **数据源假设完全错误**：proposal 反复提到 "queries `changes` SQLite table"，但确定性事实证明 `sqlite3` 符号在项目中不存在。实际数据存储在 `~/.openspec/changes/*.json`（`daemon.py:118` 处 `changes_dir = Path(home) / "openspec" / "changes"`），每个 proposal 一个 JSON 文件，包含 `change_name`、`outcome`、`started_at`、`finished_at` 等字段。所有 SQL 查询设计都是空中楼阁。
2. **历史失败模式未规避**：`dashboard-add-feedback-loop-metrics` 连续 4 次失败，教训是"verify test expectations match implementation API"。本 proposal 没有包含任何测试策略或验收测试定义，很可能重蹈覆辙。

## 建议
1. **重写 Technical Design 的数据访问层**：删除所有 SQL，改为 Python 遍历 `changes_dir.glob("*.json")` 做内存聚合。参考 `_detect_proposal_phase`（daemon.py:114-133）和 `_build_current_json`（daemon.py:136-154）中已有的 JSON 读取模式——代码库里已有两处完全相同的数据访问代码，应先提取为 `_load_all_changes(home)` 公共函数，再在此基础上做统计。
2. **补充验收测试**：在 proposal 中明确测试策略——至少需要测试空数据（无 JSON 文件时返回全零）和有数据时的聚合正确性。历史教训表明 dashboard 指标类任务最容易在 test expectations 上翻车。
