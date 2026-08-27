# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为无测试覆盖的核心模块 `zsiga/daemon.py`（1056 行，21 函数，1 类，6 个高复杂度函数）创建 `tests/test_daemon.py`，编写单元测试以覆盖公开函数和关键逻辑路径，不修改源码。

### 拆解后的子任务

- [ ] 1. **文件系统工具函数测试**（`_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `_write_daemon_state`, `acquire_lock`, `release_lock`）
  - 覆盖路径拼接、文件读写、锁的获取与释放、异常路径（文件不存在、权限错误等）
  - 预估复杂度：中, 预估 token：~4000

- [ ] 2. **提案队列扫描测试**（`_scan_proposal_queue`，CC=29）
  - 覆盖空目录、有提案目录、提案状态过滤、排序逻辑、异常目录名等分支
  - 使用 `tmp_path` 隔离文件系统
  - 预估复杂度：高, 预估 token：~5000

- [ ] 3. **状态与指标构建测试**（`_compute_uptime_seconds`, `_build_status_json`, `_build_metrics_json`）
  - 覆盖正常计算、边界值（started_at 为 None/0）、JSON 序列化输出结构验证
  - 预估复杂度：低, 预估 token：~2500

- [ ] 4. **高复杂度构建函数测试**（`_build_pipeline_status` CC=32, `_build_proposal_detail` CC=20, `_build_evolution_status` CC=11）
  - Mock 外部依赖（文件 I/O、子进程调用），覆盖主分支和错误处理分支
  - 预估复杂度：高, 预估 token：~6000

- [ ] 5. **Dashboard HTTP handler 测试**（`_serve_dashboard.do_GET` CC=15）
  - 使用 `unittest.mock` 模拟 HTTP 请求，覆盖路由分发和响应生成
  - 预估复杂度：中, 预估 token：~3000

- [ ] 6. **daemon_loop 主循环测试**（`daemon_loop` CC=38）
  - Mock 时间、文件锁、外部调用，覆盖循环入口/退出条件、idle/busy 状态切换
  - 预估复杂度：高, 预估 token：~5000

- [ ] 7. **lint 修复验证与最终集成**（运行 pytest + ruff，确保全部通过）
  - 预估复杂度：低, 预估 token：~1000

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，编写 `def test_` 函数
- 覆盖 proposal 中列出的公开函数：`_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `_write_daemon_state`, `acquire_lock`, `release_lock`, `_scan_proposal_queue`, `_compute_uptime_seconds`, `_build_status_json`, `_build_metrics_json`
- 对高 CC 函数（`_build_pipeline_status`, `_build_proposal_detail`, `_build_evolution_status`, `_serve_dashboard.do_GET`, `daemon_loop`）的测试
- 使用 mock 隔离 LLM 调用、文件 I/O、subprocess 等外部依赖
- BAC-02 要求：测试文件中必须存在 `test__lock_path`, `test__daemon_state_path`, `test__read_daemon_state` 三个函数

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复其中 2 个 lint 问题：F401 未使用 import、F541 空 f-string）
- 不添加/修改其他测试文件
- 不修改项目配置（pyproject.toml、requirements.txt）
- 不涉及 `DaemonState` 类的扩展或重构（仅按现有接口测试）

### 依赖的外部条件
- `zsiga/daemon.py` 可正常 import（无 ImportError）
- `tests/conftest_zsiga.py` 中已有的 fixture 可用
- 项目依赖已安装（httpx, pyyaml, zai-sdk 等）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 文件中包含 `test__lock_path`, `test__daemon_state_path`, `test__read_daemon_state` 三个指定测试函数
3. `python -m pytest tests/test_daemon.py` 退出码为 0（全部通过）
4. `ruff check tests/test_daemon.py` 无错误
5. 不修改 `zsiga/daemon.py` 的任何内容（git diff 验证）

### 验收方式
- BAC-01: 检查文件 `tests/test_daemon.py` 存在
- BAC-02: 检查文件中存在 `test__lock_path`, `test__daemon_state_path`, `test__read_daemon_state` 符号
- BAC-03: 检查文件中存在至少 3 个 `def test_` 函数定义
- BAC-04: 运行 `python -m pytest tests/test_daemon.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（仅读取分析）
- `pyproject.toml`
- `requirements.txt`
- `tests/conftest_zsiga.py`
- 任何其他已有测试文件

### 项目部署分支
- main

### 已知风险
- `daemon_loop`（CC=38, 258 行）是最高复杂度函数，内部可能依赖大量外部状态（锁文件、信号处理、时间循环），mock 层可能较厚，测试覆盖率可能有限
- `_build_pipeline_status`（CC=32）和 `_build_proposal_detail`（CC=20）可能引用 `zsiga/daemon.py` 内部的全局变量或闭包状态，需确认 mock 策略
- 源码中有 2 个 lint 问题（F401、F541），虽然不在 scope 内修复，但可能影响测试编写时的 import 行为
- `DaemonState` 类 methods 列表为空（静态分析数据），可能是 dataclass 或 NamedTuple，需实际确认后决定测试策略

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考（同类任务 verify-layer0-with-tests 曾失败，但失败原因为覆盖率不足而非测试编写本身；本次按新 proposal 独立估算）
