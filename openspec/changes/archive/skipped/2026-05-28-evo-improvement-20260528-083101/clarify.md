# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1085 行, 21 函数, 1 类）添加单元测试文件 `tests/test_daemon.py`，覆盖公开/内部函数，优先覆盖高圈复杂度函数。不修改源码。

### 拆解后的子任务

- [ ] 1. **工具函数与状态序列化测试** — 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_write_daemon_state`、`_compute_uptime_seconds`。验证路径拼接、JSON 读写、边界值（空文件/损坏 JSON）。(预估复杂度：低, 预估 token：~4000)
- [ ] 2. **文件锁管理测试** — 覆盖 `acquire_lock`、`release_lock`。验证锁文件创建/释放、文件描述符关闭、并发场景下的行为。使用 `tmp_path` 隔离文件系统。(预估复杂度：中, 预估 token：~3000)
- [ ] 3. **Proposal 队列扫描测试** — 覆盖 `_scan_proposal_queue`（CC=29, 90 行）。构造多种目录结构（空队列/正常队列/损坏 proposal 文件/混合状态），验证过滤、排序、状态解析逻辑。mock `config.load_config()`。(预估复杂度：高, 预估 token：~6000)
- [ ] 4. **状态构建器测试** — 覆盖 `_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`（CC=32）、`_build_proposal_detail`（CC=20）、`_build_evolution_status`（CC=11）。构造 mock daemon_state / metrics / DB 查询结果，验证 JSON 输出结构与字段完整性。(预估复杂度：高, 预估 token：~6000)
- [ ] 5. **pytest 执行验证** — 确认 `python -m pytest tests/test_daemon.py` 退出码 0，无 import 错误、无 fixture 冲突、无与现有 daemon 测试文件的交叉依赖。(预估复杂度：低, 预估 token：~1000)

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，编写独立单元测试
- 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`（BAC-02 强制要求）
- 额外覆盖 `_write_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status`、`_compute_uptime_seconds`
- 使用 `unittest.mock` / `monkeypatch` / `tmp_path` 隔离外部依赖
- 至少 3 个 `def test_` 函数（BAC-03 最低门槛）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复其 2 个 lint 问题：L362 F401 `glob` unused、L948 F541 f-string without placeholders）
- 不覆盖 `daemon_loop`（CC=43, 284 行）— 过于复杂，需要 mock 完整 HTTP 服务 + LLM 调用链 + 状态机循环，超出单次任务合理范围
- 不覆盖 `_serve_dashboard.do_GET`（CC=16, 67 行）— 需要构造完整 HTTP 请求上下文，属于集成测试范畴
- 不修改或合并已有的 daemon 测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）

### 依赖的外部条件
- `zsiga/daemon.py` 中目标函数的签名和导入路径保持稳定
- `tests/conftest_zsiga.py` 提供的 pytest 基础设施（如有 fixture 冲突需适配）
- 已有 3 个 daemon 测试文件（~876 行）覆盖了部分函数（`_write_daemon_state`、`_read_daemon_state`、`daemon_loop`），新测试应避免完全重复已有用例，侧重补充未覆盖路径

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含有效的 Python 测试代码
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个函数名（BAC-02）
3. 文件中至少 3 个 `def test_` 函数（BAC-03）
4. `python -m pytest tests/test_daemon.py` 退出码 0（BAC-04）
5. 测试通过 `ruff check` 无 lint 错误

### 验收方式
- `test -f tests/test_daemon.py` 验证文件存在
- `grep -c 'def test_' tests/test_daemon.py` 验证测试数量 ≥ 3
- `python -m pytest tests/test_daemon.py -v` 验证全部通过
- `ruff check tests/test_daemon.py` 验证代码质量
- 与已有 daemon 测试文件做差异化审查，确认无低价值重复

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析
- `tests/test_daemon_state.py` — 已有测试
- `tests/test_daemon_scheduling.py` — 已有测试
- `tests/test_daemon_cycle_resilience.py` — 已有测试
- `tests/conftest_zsiga.py` — 共享 fixture

### 项目部署分支
- `main`

### 已知风险
- **已有覆盖重叠**：`tests/test_daemon_state.py`（242 行, 10 测试）已覆盖 `_write_daemon_state`、`_read_daemon_state`、`_daemon_state_path`，新测试可能产生重复用例。应优先覆盖已有文件未涉及的函数（如 `_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`）
- **daemon 模块稳定性**：daemon.py 近期有 `cycle_error` 反复失败记录（2026-05-27 连续 3 次），说明模块状态管理复杂，mock 不精确可能掩盖真实问题
- **高 CC 函数测试难度**：`_build_pipeline_status`（CC=32）依赖 SQLite DB 查询、文件系统扫描、daemon_state 读取等多重外部依赖，mock 链条较长
- **导入依赖链**：daemon.py 可能依赖 `zsiga.config`、`zsiga.metrics.db`、`zsiga.logging` 等模块，需要在测试中 mock 这些导入

### 预估 token 消耗
- prompt: ~12000（源码分析 + 上下文）
- completion: ~8000（测试代码生成）
- 数据来源: 无历史参考（同类 daemon 测试任务无直接成功记录）
