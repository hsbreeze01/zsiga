# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类）创建单元测试文件 `tests/test_daemon.py`，覆盖当前未被任何测试文件触及的 8 个函数。已有 3 个测试文件（`test_daemon_state.py` 11 tests、`test_daemon_scheduling.py` 9 tests、`test_daemon_cycle_resilience.py` 5 tests）覆盖了 `_write_daemon_state`、`daemon_loop` 的调度逻辑和错误韧性，但以下函数仍无直接测试覆盖。

### 拆解后的子任务

- [ ] 1. **路径与状态读取工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()` 三个纯路径/IO 工具函数（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **文件锁获取/释放测试** — 覆盖 `acquire_lock()` 和 `release_lock(fd)`，使用 tmp_path 隔离文件系统（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 3. **指标与状态构建函数测试** — 覆盖 `_compute_uptime_seconds()`、`_build_status_json()`、`_build_metrics_json()`，mock 外部依赖（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 4. **pytest 全量通过验证** — 确保新建测试文件通过 `pytest tests/test_daemon.py` 且 ruff 无 lint 错误（预估复杂度：低, 预估 token：~1000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含 8+ 个 `def test_` 函数，覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`
- 遵循项目已有测试模式：`monkeypatch` + `tmp_path` 替换路径、`unittest.mock.patch` 隔离外部依赖、`class Test*` 分组
- 确保新建文件 ruff 无 lint 错误

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（含修复 2 个已知 lint 问题）
- 不覆盖已有测试文件已覆盖的函数（`_write_daemon_state`、`daemon_loop` 调度/韧性逻辑）
- 不覆盖高 CC 函数（`_scan_proposal_queue` CC=29、`_build_pipeline_status` CC=32 等）— 这些依赖链过深，宜后续独立 proposal 处理
- 不创建 `test_daemon.py` 以外的文件

### 依赖的外部条件
- `zsiga/daemon.py` 源码在实现期间不可变
- 项目 Python >= 3.10 环境，pytest + ruff 可用
- 已有 `tests/conftest_zsiga.py` 提供共享 fixture

## 目标

### 成功标准
1. `tests/test_daemon.py` 存在且包含至少 8 个 `def test_` 函数
2. `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个测试函数存在（BAC-02）
3. `python -m pytest tests/test_daemon.py` 退出码 0（BAC-04）
4. `ruff check tests/test_daemon.py` 无错误
5. 每个被测函数至少有 1 个直接导入调用的测试用例（非间接覆盖）

### 验收方式
- `test -f tests/test_daemon.py && echo OK`
- `grep -c 'def test_' tests/test_daemon.py` >= 8
- `grep -q 'def test__lock_path' tests/test_daemon.py && grep -q 'def test__daemon_state_path' tests/test_daemon.py && grep -q 'def test__read_daemon_state' tests/test_daemon.py`
- `python -m pytest tests/test_daemon.py -x -q` 退出码 0
- `ruff check tests/test_daemon.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析，不做任何修改
- `tests/test_daemon_state.py`、`tests/test_daemon_scheduling.py`、`tests/test_daemon_cycle_resilience.py` — 已有测试文件不动

### 项目部署分支
deploy

### 已知风险
- **循环空转历史**：此 proposal 已被自演进引擎生成 20+ 轮，均未成功交付。本轮 BAC 已收紧，需确保实现质量达标而非仅凑数
- **daemon.py 内部耦合**：部分函数（如 `_build_status_json`、`_build_metrics_json`）可能依赖模块级全局状态，需要仔细 mock
- **已有覆盖重叠**：`test_daemon_state.py` 已间接测试了 `_daemon_state_path()` 的路径生成逻辑，新建测试需避免纯重复但应提供直接测试

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（同类 proposal 20+ 轮均未成功交付，无可参考 token 消耗数据）
