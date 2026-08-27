## Verdict: PUSHBACK

## 我的判断

这个 proposal 结构工整、BAC 写得规范、技术方案清晰——乍看是个不错的 proposal。但它有一个致命问题：**前提是错的**。它声称 `zsiga/daemon.py` "缺少测试文件"，暗示该模块完全没有测试覆盖。事实上，代码库中已存在 **3 个专门的 daemon 测试文件，合计约 876 行测试代码**：

- `tests/test_daemon_state.py`（242 行）— 覆盖 `_write_daemon_state`、`_read_daemon_state`、调度统计字段
- `tests/test_daemon_scheduling.py`（421 行）— 覆盖 `daemon_loop` 的智能调度策略（idle poll、busy cycle、safety valve、cooldown）
- `tests/test_daemon_cycle_resilience.py`（213 行）— 覆盖错误隔离、结构性诊断、lesson 记录
- `tests/test_dashboard_api.py` 中还有 `test_daemon_fields_present`

我不是说 daemon.py 已经 100% 覆盖——确实还有 `_lock_path`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_build_pipeline_status`、`_build_proposal_detail` 等函数缺少直接测试。但 proposal 完全无视已有覆盖，没能区分"已有测试的函数"和"真正缺少测试的函数"，这让人质疑其静态分析数据的可靠性。

## 评分详情
- 可行性: 2/2 -- `zsiga/daemon.py` 确认存在（1110行），目标函数全部确认存在，测试基础设施完备
- 可执行性: 2/2 -- 有明确的 target file、函数列表、mock 隔离策略，BAC 中的测试函数名也具体
- 能力匹配: 1/2 -- 无直接可比的"为 daemon 添加测试"的历史记录，但测试编写属于常规能力
- 历史风险: 1/2 -- 无完全相同的失败记录，但 proposal 标注为"自演进引擎生成"，auto-generated 风险 -1。`verify-layer0-with-tests` 有 verify 阶段失败先例
- 范围合理性: 1/2 -- scope 表面清晰（只建新文件不修改源码），但**完全无视 3 个已有的 daemon 测试文件**（共 876 行），问题描述有误导性。如果这只是一个补漏提案，应该明确说明"哪些函数已有测试、哪些还没有"
- 验收可测性: 2/2 -- 4 条 BAC 全部是 binary check（文件存在、符号存在、≥3 个 test_ 函数、pytest 退出码 0），格式规范
- **总分: 9/12**

## 疑虑
1. **前提错误**：Proposal 声称 daemon.py "缺少测试文件"，但 `test_daemon_state.py`（242L）、`test_daemon_scheduling.py`（421L）、`test_daemon_cycle_resilience.py`（213L）已提供大量覆盖。`_write_daemon_state` 已有 11 个测试方法，`daemon_loop` 的调度逻辑有 8 个测试场景。Proposal 基于虚假前提定位问题。
2. **静态分析盲区**：Proposal 引用了静态分析数据（"21 函数、1 类"），但其分析工具无法识别已有测试文件中的覆盖关系。这说明自动生成 pipeline 的 gap analysis 能力不足——它只检查了"有没有 `test_daemon.py` 这个文件名"，没有检查"daemon 相关测试是否已存在"。
3. **重叠风险**：BAC-02 要求 `test__read_daemon_state` 存在于新文件中，但 `test_daemon_state.py` 已间接测试了 `_read_daemon_state`（通过 `_write_daemon_state` 的 round-trip 测试）。新文件可能与已有测试功能重叠，增加维护负担而不增加覆盖价值。
4. **真正缺少覆盖的函数没有被优先列出**：`_lock_path`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_health_check`、`_build_pipeline_status`、`_build_proposal_detail` 确实没有直接测试，但 proposal 没有做 gap analysis 来区分这些。

## 建议
1. **重写 Problem 部分**，承认已有 3 个 daemon 测试文件的存在，明确列出"已有覆盖的函数" vs "仍缺覆盖的函数"，让 reviewer 能判断增量价值。
2. **将 BAC-02 调整为覆盖真正缺测的函数**，例如 `test__lock_path`、`test__scan_proposal_queue`、`test__compute_uptime_seconds`、`test__health_check` 等，而非已被 `test_daemon_state.py` 间接覆盖的 `_read_daemon_state`。
3. **考虑是否需要新文件**：如果增量测试数量不多（<10 个），可以追加到 `test_daemon_state.py` 或新建 `test_daemon_api.py`，而非笼统的 `test_daemon.py`（容易与已有文件混淆）。
4. **在 Proposal 中明确标注** "此 proposal 与 `test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py` 的关系"。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 为已有代码添加测试时在 verify 阶段失败
- Evolution: identified recurring failure daemon.cycle_error (2026-05-27~29, 多次) — daemon 相关的自动修复循环失败，提醒 auto-generated daemon 类 proposal 需格外谨慎
