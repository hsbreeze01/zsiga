# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行、21 函数、1 类）创建单元测试文件 `tests/test_daemon.py`，覆盖未被现有测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）触及的公开与私有函数。优先覆盖 6 个高圈复杂度函数（CC > 10），使用 mock 隔离文件 I/O、subprocess 等外部依赖。

### 拆解后的子任务

- [ ] 1. **路径与锁工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`、`acquire_lock()`、`release_lock(fd)`。验证路径拼接正确性、锁文件创建/释放、daemon state JSON 读写。BAC-02 要求的 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 均在此任务中实现。（预估复杂度：低, 预估 token：~4000）
- [ ] 2. **提案队列扫描器测试** — 覆盖 `_scan_proposal_queue(changes_dir)`（CC=29，90 行）。Mock 文件系统，验证空目录/正常提案/暂停提案/连续失败提案/损坏 `.phase_state` 等分支路径。返回队列条目的结构校验（name/project/phase/lifecycle/consecutive_fails 等字段）。（预估复杂度：高, 预估 token：~6000）
- [ ] 3. **状态与指标构建器测试** — 覆盖 `_compute_uptime_seconds(started_at)`、`_build_status_json()`、`_build_metrics_json()`。验证 uptime 计算（含边界：刚启动/运行数小时）、JSON 输出字段完整性、指标聚合正确性。（预估复杂度：中, 预估 token：~4000）
- [ ] 4. **Pipeline 与进化状态详情测试** — 覆盖 `_build_pipeline_status()`（CC=32）、`_build_proposal_detail()`（CC=20）、`_build_evolution_status()`（CC=11）。Mock SQLite 数据库查询（`zsiga/metrics/db.py` 的 `changes` 表），验证空结果集/多变更记录/阶段 JSON 解析/异常降级等分支。（预估复杂度：高, 预估 token：~6000）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，编写单元测试
- 使用 `unittest.mock`（mock/patch）隔离文件 I/O、subprocess、SQLite 查询
- 覆盖 BAC-02 指定的 3 个测试函数名
- 覆盖高 CC 函数的核心分支路径
- 确保所有测试独立运行，无运行时环境依赖

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复 L362 F401 和 L965 F541 两个 lint 问题）
- 不修改已有的 3 个 daemon 测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）
- 不测试 `daemon_loop`（CC=51）的全部分支——已有 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 覆盖调度与恢复逻辑
- 不测试 `_serve_dashboard.do_GET`（CC=16）的 HTTP 层——涉及 socket 服务器 mock，投入产出比低
- 不涉及其他模块的测试

### 依赖的外部条件
- `zsiga/daemon.py` 模块可正常 import（无循环依赖）
- `tests/conftest_zsiga.py` 提供的共享 fixture 可用
- 项目 Python 环境已安装 `pytest`、`ruff`

## 目标

### 成功标准
1. 文件 `tests/test_daemon.py` 存在且包含有效 Python 测试代码
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个函数（BAC-02）
3. 文件中包含至少 3 个 `def test_` 函数（BAC-03）
4. `python -m pytest tests/test_daemon.py` 退出码 0（BAC-04）
5. 测试覆盖至少 10 个 daemon.py 中的函数/方法
6. 所有测试通过 `ruff check` 无错误

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 确认测试函数数量 ≥ 3
- `grep 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py` 确认 BAC-02 函数名存在
- `python -m pytest tests/test_daemon.py -v` 退出码 0 确认全部通过
- `ruff check tests/test_daemon.py` 无错误确认代码规范

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（仅读取分析）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `tests/test_spec_evo_improvement_20260530_111612__daemon_path_and_lock.py`（同 change 已生成的 spec 测试）

### 项目部署分支
`deploy`

### 已知风险
- **与现有测试重叠**：`test_daemon_state.py` 已覆盖 `_write_daemon_state`，新建测试应跳过该函数避免重复
- **同 change 已有 spec 测试**：`test_spec_evo_improvement_20260530_111612__daemon_path_and_lock.py` 可能已覆盖部分路径/锁函数，需检查避免完全重复的断言
- **高 CC 函数 mock 复杂度**：`_build_pipeline_status`（CC=32）和 `_scan_proposal_queue`（CC=29）分支众多，完整覆盖需要大量 mock setup，可能超出单轮 token 预算
- **daemon.py 内部耦合**：多个函数共享 `data/` 目录路径约定和 `DaemonState` 类，测试需注意工作目录隔离（`tmp_path` fixture）

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类 daemon 测试任务无成功落地记录，但 archive 中有多次 skipped 的实现代码可参考模式）
