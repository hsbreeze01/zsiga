# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1085 行，21 函数，1 类）添加单元测试文件 `tests/test_daemon.py`。Proposal 声称该模块缺少测试，但**事实是已有 3 个 daemon 测试文件共 ~876 行**（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`），覆盖了 `_write_daemon_state`、`_read_daemon_state`、`_daemon_state_path`、`daemon_loop` 调度逻辑等。**真正的覆盖缺口在于高复杂度状态构建函数和队列扫描函数**。本次需求应聚焦于填补这些缺口，而非重复已有覆盖。

### 拆解后的子任务

- [ ] 1. **路径/状态工具函数补测**（预估复杂度：低, 预估 token：~1500）
  - 覆盖目标：`_lock_path()`（L34-L39）、`_daemon_state_path()`（L42-L45）
  - 说明：这两个纯路径构造函数在现有测试中仅作为 monkeypatch 目标被间接使用，缺少直接行为验证（返回值格式、路径拼接正确性）。`_read_daemon_state()` 已在 `test_daemon_state.py` 中有间接覆盖，可酌情补充边界情况（文件不存在、空文件、损坏 JSON）。
  - 文件范围：`tests/test_daemon.py`（新建）

- [ ] 2. **队列扫描逻辑测试**（预估复杂度：高, 预估 token：~4000）
  - 覆盖目标：`_scan_proposal_queue(changes_dir)`（L122-L211, CC=29, 90L）
  - 需 mock 的依赖：`config.load_config()`（获取 changes_dir 默认值）、文件系统（`os.listdir`/`os.path.join`）、`os.path.isdir`
  - 测试场景：空目录、仅含有效 proposal 子目录、混合有效/无效条目、损坏的 proposal.yaml、嵌套目录结构、无 read 权限
  - 文件范围：`tests/test_daemon.py`

- [ ] 3. **Pipeline/Evolution 状态构建器测试**（预估复杂度：高, 预估 token：~5000）
  - 覆盖目标：`_build_pipeline_status()`（L356, CC=32, 103L）、`_build_proposal_detail()`（L529, CC=20, 76L）、`_build_evolution_status()`（L638, CC=11, 64L）
  - 需 mock 的依赖：`metrics.db.load_all_changes()`、`os.path.exists`/`os.listdir`、config 加载、SQLite 查询
  - 测试场景：无历史变更记录、单条/多条变更记录、不同 proposal 状态（pending/running/pass/fail）、evolution 开关开启/关闭、数据缺失字段
  - 文件范围：`tests/test_daemon.py`

- [ ] 4. **指标计算与状态 JSON 输出测试**（预估复杂度：中, 预估 token：~2500）
  - 覆盖目标：`_compute_uptime_seconds()`（L214-L226）、`_build_status_json()`（L229-L244）、`_build_metrics_json()`（L249-L262）
  - 需 mock 的依赖：`_read_daemon_state()`（已由任务1覆盖）、`_build_pipeline_status()`（任务3覆盖）、`_build_evolution_status()`（任务3覆盖）
  - 测试场景：刚启动（started_at=now）、长时间运行、daemon_state 为空、各字段边界值
  - 文件范围：`tests/test_daemon.py`

- [ ] 5. **文件锁管理测试**（预估复杂度：中, 预估 token：~2000）
  - 覆盖目标：`acquire_lock()`（L94-L109）、`release_lock(fd)`（L112-L119）
  - 需 mock 的依赖：`_lock_path()`（monkeypatch 到 tmp_path）、`os.open`/`fcntl.flock`
  - 测试场景：正常获取/释放、锁文件不存在时创建、并发锁竞争（EAGAIN）、fd 关闭后释放
  - 文件范围：`tests/test_daemon.py`

- [ ] 6. **Dashboard HTTP handler 测试**（预估复杂度：中, 预估 token：~2500）
  - 覆盖目标：`_serve_dashboard.do_GET()`（L726, CC=16, 67L）
  - 需 mock 的依赖：`_build_status_json()`、`_build_metrics_json()`、`http.server.BaseHTTPRequestHandler`
  - 测试场景：`/status` 路径返回 JSON、`/metrics` 路径返回 JSON、未知路径返回 404、响应头 Content-Type 正确
  - 文件范围：`tests/test_daemon.py`

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含对 `zsiga/daemon.py` 中未被现有测试覆盖的函数的单元测试
- 重点覆盖 6 个高 CC 函数（CC>10）中的未测试分支
- 路径工具函数（`_lock_path`、`_daemon_state_path`）的直接行为验证
- 文件锁管理（`acquire_lock`、`release_lock`）的隔离测试

### OUT of scope
- **不修改** `zsiga/daemon.py` 源码（包括不修复其 2 个 lint 问题：L362 F401、L948 F541）
- **不重复**已有测试文件的覆盖内容（`test_daemon_state.py` 的 `_write_daemon_state` 测试、`test_daemon_scheduling.py` 的调度测试、`test_daemon_cycle_resilience.py` 的错误恢复测试）
- **不修改**现有 3 个 daemon 测试文件
- `daemon_loop`（CC=43, L802-L1085）的完整集成测试 — 已有 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 覆盖核心路径，本次仅在任务3中通过 mock 间接覆盖其调用的子函数
- 不涉及 `DaemonState` dataclass 的独立测试（仅 4 行定义，已被现有测试间接覆盖）

### 依赖的外部条件
- 现有测试基础设施：`tests/conftest_zsiga.py` 提供 pytest fixtures
- `zsiga/daemon.py` 源码接口稳定（函数签名不变）
- `monkeypatch` 和 `unittest.mock` 可用于隔离文件 I/O、config 加载、SQLite 查询
- `tmp_path` fixture 可用于文件锁测试的临时目录

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥6 个 `def test_` 函数（对应 6 个子任务的核心场景）
2. 测试覆盖至少 3 个高 CC 函数（CC>10）的关键分支：`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`
3. 所有测试使用 mock 隔离外部依赖，可独立运行，不依赖运行时环境（无真实文件 I/O、无真实 config 加载、无真实 LLM 调用）
4. `python -m pytest tests/test_daemon.py` 退出码 0
5. 不引入新的 lint 问题（`ruff check tests/test_daemon.py` 通过）

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 输出 ≥6
- `grep -E 'test__scan_proposal_queue|test__build_pipeline_status|test__build_proposal_detail' tests/test_daemon.py` 确认覆盖高 CC 函数
- `python -m pytest tests/test_daemon.py -v` 退出码 0 且无 SKIP/WARNING
- `ruff check tests/test_daemon.py` 无输出

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 只读分析，不修改源码
- `tests/test_daemon_state.py` — 现有测试不修改
- `tests/test_daemon_scheduling.py` — 现有测试不修改
- `tests/test_daemon_cycle_resilience.py` — 现有测试不修改
- `tests/conftest_zsiga.py` — 共享 fixture 不修改

### 项目部署分支
- `main`

### 已知风险
- **已有覆盖重复风险**：`_read_daemon_state`、`_daemon_state_path` 已在现有测试中被间接覆盖。若新测试与现有测试逻辑重复，会增加维护负担。应只补充边界情况和直接行为验证。
- **高 CC 函数 mock 复杂度**：`_build_pipeline_status`（CC=32）内部依赖 SQLite 查询、文件系统遍历、config 加载等多层依赖，mock 链可能较长且脆弱。
- **daemon.py 自身有 2 个 lint 问题**（L362 F401、L948 F541），虽然不在本 scope 内修复，但需要在测试中确保不触发这些路径。
- **proposal gate 历史风险**：同类 `add-tests-*` proposal 已被多次 PUSHBACK/REJECT（核心原因：与已有测试重复、BAC 质量低）。本次需确保真正填补覆盖缺口。

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考（同类 proposal 均未执行成功，无历史消耗数据）
