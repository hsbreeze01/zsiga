# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）中尚未被现有测试文件覆盖的函数新建 `tests/test_daemon.py` 单元测试。现有 3 个测试文件（`test_daemon_state.py` 242L、`test_daemon_scheduling.py` 421L、`test_daemon_cycle_resilience.py` 213L）已覆盖 `_write_daemon_state` 和 `daemon_loop` 的调度/韧性逻辑，但以下函数缺少直接测试覆盖：`_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`、`_build_proposal_detail`。

### 拆解后的子任务

- [ ] 1. **路径工具与状态读取测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()` 三个纯函数/简单函数：验证 ZSIGA_HOME 环境变量拼接、路径结构、JSON 解析正常路径及文件不存在/格式错误异常路径（预估复杂度：低, 预估 token：~2000）
- [ ] 2. **锁管理测试** — 覆盖 `acquire_lock()` 和 `release_lock(fd)`：mock `fcntl.flock`，验证锁文件创建、PID 写入、释放时关闭 fd、异常时清理（预估复杂度：低, 预估 token：~2000）
- [ ] 3. **队列扫描测试** — 覆盖 `_scan_proposal_queue(changes_dir)`（CC=29）：mock 目录结构与 proposal 状态文件，验证 proposal 过滤（pending/非 pending）、排序、`consecutive_fails` 计数、空目录处理、边界条件（预估复杂度：高, 预估 token：~3000）
- [ ] 4. **状态构建与指标计算测试** — 覆盖 `_compute_uptime_seconds(started_at)`、`_build_status_json()`、`_build_metrics_json()`：验证时间计算精度、JSON 结构完整性、字段类型正确性、空值/默认值处理（预估复杂度：中, 预估 token：~2500）
- [ ] 5. **Pipeline 状态与 Proposal 详情测试** — 覆盖 `_build_pipeline_status()`（CC=32）和 `_build_proposal_detail()`（CC=20）：mock SQLite 查询结果，验证空结果集处理、多 proposal 状态映射、字段完整性、异常数据库路径处理（预估复杂度：高, 预估 token：~3000）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，为上述 11 个未覆盖函数编写单元测试
- 使用 `monkeypatch`、`unittest.mock.patch`、`tmp_path` 等 pytest 机制隔离外部依赖
- 每个测试可独立运行，不依赖运行时环境或网络
- 遵循项目已有测试模式（class-based 组织，如 `TestLockPath`、`TestScanProposalQueue`）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括不修复 L362 F401 和 L965 F541 两个 lint 问题）
- 不修改已有的 3 个 daemon 测试文件
- 不覆盖 `daemon_loop`（CC=51）、`_build_evolution_status`（CC=11）、`_serve_dashboard.do_GET`（CC=16）——这些由现有测试文件覆盖或需独立 proposal
- 不覆盖 `_write_daemon_state`——已由 `test_daemon_state.py` 全面覆盖
- 不涉及 dashboard HTML 或 API 路由变更

### 依赖的外部条件
- `zsiga/daemon.py` 源码在实现期间不发生破坏性重构
- 项目 Python 环境 ≥ 3.10，pytest 可用
- `fcntl` 模块可用（Linux 环境，非 Windows）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个具名测试函数
2. 文件中至少包含 3 个 `def test_` 函数（实际预期覆盖 11 个函数，约 15-25 个测试用例）
3. `python -m pytest tests/test_daemon.py` 退出码为 0，所有测试通过
4. 新测试与已有 3 个 daemon 测试文件不产生冲突或重复

### 验收方式
- 检查 `tests/test_daemon.py` 文件存在性
- `grep -c 'def test_' tests/test_daemon.py` ≥ 3
- `grep -q 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py`
- `python -m pytest tests/test_daemon.py -v` 退出码 0
- `python -m pytest tests/test_daemon.py tests/test_daemon_state.py tests/test_daemon_scheduling.py tests/test_daemon_cycle_resilience.py` 全部通过（无冲突）

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析
- `tests/test_daemon_state.py` — 已有覆盖，不碰
- `tests/test_daemon_scheduling.py` — 已有覆盖，不碰
- `tests/test_daemon_cycle_resilience.py` — 已有覆盖，不碰
- `zsiga/config.py`、`zsiga/pipeline/` 下所有文件

### 项目部署分支
- `deploy`

### 已知风险
- **自演进循环风险**：此 proposal 已被 PUSHBACK 至少 14 次，是重复最多的 proposal 之一。若 BAC 仍不满足，将继续循环生成
- **已有测试文件冲突**：3 个已有 daemon 测试文件通过 `monkeypatch.setattr("zsiga.daemon._daemon_state_path", ...)` 替换模块级路径函数，新测试需确保 monkeypatch 作用域不互相干扰
- **高 CC 函数测试质量**：`_scan_proposal_queue`(CC=29) 和 `_build_pipeline_status`(CC=32) 分支密集，mock 需精确覆盖关键路径，否则测试沦为形式
- **`fcntl` 平台限制**：`acquire_lock`/`release_lock` 依赖 `fcntl.flock`，在非 POSIX 环境下不可用

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类 proposal 从未成功执行过）
