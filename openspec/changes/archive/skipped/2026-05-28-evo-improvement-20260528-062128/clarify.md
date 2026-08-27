# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1085 行，21 函数，1 类 `DaemonState`）创建单元测试文件 `tests/test_daemon.py`。模块已有 3 个侧面测试文件（`test_daemon_state.py` 242L、`test_daemon_scheduling.py` 421L、`test_daemon_cycle_resilience.py` 213L），但缺少一个综合性的 `test_daemon.py`，且多个高复杂度函数（CC 11~43）缺乏直接测试覆盖。

### 拆解后的子任务

- [ ] 1. **路径与状态读取工具函数测试** — 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`（预估复杂度：低，预估 token：~3000）
  - 文件范围：`tests/test_daemon.py`（新建），读取 `zsiga/daemon.py` L34-L56
  - 验证点：路径拼接正确性（monkeypatch `os.path.expanduser`）、空/损坏状态文件处理、正常 JSON 解析
  - 满足 BAC-02、BAC-03 最低门槛

- [ ] 2. **状态持久化与锁管理测试** — 覆盖 `_write_daemon_state`、`acquire_lock`、`release_lock`（预估复杂度：中，预估 token：~5000）
  - 文件范围：`tests/test_daemon.py`，读取 `zsiga/daemon.py` L59-L119
  - 验证点：`_write_daemon_state` 写入 JSON 格式正确性（使用 `tmp_path`）、字段完整性（started_at/cycle/state 等 10 个参数）；`acquire_lock` 创建锁文件、`release_lock` 关闭文件描述符并删除锁
  - 需 mock：文件系统（`tmp_path` fixture）、`os.open`/`fcntl.flock`

- [ ] 3. **提案队列扫描与状态构建器测试** — 覆盖 `_scan_proposal_queue`(CC=29)、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`（预估复杂度：高，预估 token：~8000）
  - 文件范围：`tests/test_daemon.py`，读取 `zsiga/daemon.py` L122-L262
  - 验证点：`_scan_proposal_queue` 空队列返回空列表、正常队列按 priority 排序、损坏 proposal 文件跳过、多个 proposal 的排序逻辑；`_compute_uptime_seconds` 计算 uptime（mock time.time）；`_build_status_json`/`_build_metrics_json` 输出结构验证
  - 需 mock：`os.listdir`、`os.path.isdir`、`config.load_config()`、`json.load`、`time.time`

- [ ] 4. **Pipeline 状态详情构建器测试** — 覆盖 `_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20)、`_build_evolution_status`(CC=11)（预估复杂度：高，预估 token：~8000）
  - 文件范围：`tests/test_daemon.py`，读取 `zsiga/daemon.py` L356-L701
  - 验证点：`_build_pipeline_status` 处理空 changes 目录、有 pending/completed/failed 变更的场景、各阶段状态聚合；`_build_proposal_detail` 正常 proposal 解析、缺失字段容错；`_build_evolution_status` evolution 指标计算
  - 需 mock：`metrics.db.load_all_changes()`、`os.path.exists`、`json.load`、`config.load_config()`、文件系统

- [ ] 5. **Dashboard HTTP 处理器与 daemon 主循环测试** — 覆盖 `_serve_dashboard.do_GET`(CC=16)、`daemon_loop`(CC=43) 的关键分支（预估复杂度：高，预估 token：~6000）
  - 文件范围：`tests/test_daemon.py`，读取 `zsiga/daemon.py` L726-L1085
  - 验证点：`_serve_dashboard.do_GET` 各 URL 路由分发（/status、/metrics、/proposals）、404 处理；`daemon_loop` 的空闲循环、单次 change 处理、cap_exceeded 中断（仅覆盖主流程，不追求全分支）
  - 需 mock：`http.server.BaseHTTPRequestHandler`、`subprocess.run`、LLM 调用链、`_scan_proposal_queue`、`acquire_lock`/`release_lock`

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含 5 个测试类对应上述 5 个子任务
- 覆盖 `zsiga/daemon.py` 中 15+ 个函数的直接测试（包括 BAC 要求的 3 个）
- 使用 `tmp_path`、`monkeypatch`、`unittest.mock` 隔离外部依赖
- 确保与已有 3 个 `test_daemon_*.py` 不产生测试内容重叠（聚焦未覆盖函数）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复其中 2 个 lint 问题：L362 F401、L948 F541）
- 不修改已有的 `test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`
- 不为 `DaemonState` dataclass 编写重复测试（已在 `test_daemon_state.py` 中覆盖）
- 不修改 `conftest_zsiga.py` 或其他测试基础设施

### 依赖的外部条件
- `zsiga/daemon.py` 在实现期间不被其他并行的 proposal 修改
- `pytest`、`unittest.mock` 可用（项目已有 `conftest_zsiga.py` 支持）
- `tmp_path` fixture 可用（pytest 内置）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含至少 15 个 `def test_` 函数
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个 BAC 指定函数
3. `python -m pytest tests/test_daemon.py` 退出码 0
4. `ruff check tests/test_daemon.py` 无错误
5. 至少覆盖 3 个高 CC 函数（`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`）的直接测试

### 验收方式
- `test -f tests/test_daemon.py` 验证文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 15
- `grep 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py` 验证 BAC-02
- `python -m pytest tests/test_daemon.py -v` 退出码 0
- `ruff check tests/test_daemon.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（只读分析）
- `tests/test_daemon_state.py`、`tests/test_daemon_scheduling.py`、`tests/test_daemon_cycle_resilience.py`（已有测试）
- `tests/conftest_zsiga.py`（共享基础设施）

### 项目部署分支
- main

### 已知风险
- **高复杂度函数 mock 链路长**：`daemon_loop`(CC=43) 内部调用 `acquire_lock`→`_scan_proposal_queue`→`_build_pipeline_status`→LLM→subprocess 等多层嵌套，mock 不精确可能掩盖真实问题。建议：先覆盖子任务 1-4 的独立函数，子任务 5 仅覆盖 `daemon_loop` 的主流程（空闲/单次处理），不追求全分支覆盖
- **已有测试重叠**：`test_daemon_state.py` 已覆盖 `_write_daemon_state` 和部分 `_read_daemon_state`，需确保新测试不重复已有场景，而是补充未覆盖的边界条件
- **自演进引擎历史**：`add-tests-daemon` proposal 已被 pushback 4 次，主要原因为 BAC 过于宽松（仅要求 3 个简单函数）。本次 clarify 将最低门槛提升至 15 个测试函数，覆盖 15+ 个目标函数

### 预估 token 消耗
- prompt: ~12000（读取 daemon.py 全量 + 测试编写上下文）
- completion: ~10000（~300 行测试代码）
- 数据来源: 无历史参考（同类 proposal 均未执行成功）
