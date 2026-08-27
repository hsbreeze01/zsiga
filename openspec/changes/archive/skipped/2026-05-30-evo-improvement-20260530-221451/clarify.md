# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数，3 个类）添加单元测试文件 `tests/test_transport.py`，覆盖所有公开 API：`Transport` 基类、`LocalTransport`、`SSHTransport`、`create_transport()` 工厂函数。仅添加测试，不修改源码。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + LocalTransport 测试**（预估复杂度：低, 预估 token：~3000 / 无历史参考）
  - 覆盖 `Transport.run_shell` 抛出 `NotImplementedError`、`Transport.close` 空实现
  - 覆盖 `LocalTransport.run_shell` 正常返回（mock `subprocess.run`）、传入 cwd/timeout/stdin 参数、shell=True 行为
  - 文件范围：`tests/test_transport.py`（新建）

- [ ] 2. **SSHTransport 完整测试**（预估复杂度：中, 预估 token：~5000 / 无历史参考）
  - 覆盖 `__init__` 初始化（host/key/user/port 属性）
  - 覆盖 `_target` 属性拼接逻辑（user@host）
  - 覆盖 `_base_args` 返回 ssh 基础参数列表
  - 覆盖 `_ensure_control` 控制路径创建逻辑（mock `tempfile.mktemp`、`subprocess.run`）
  - 覆盖 `run_shell` 远程命令执行（正常路径 + `TimeoutExpired` → exit_code=-1 + `OSError` → exit_code=-1）
  - 覆盖 `close` 关闭控制路径（ssh -O exit）
  - 文件范围：`tests/test_transport.py`（新建）

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~1500 / 无历史参考）
  - 覆盖 ssh=None 或无 ssh 属性 → 返回 `LocalTransport`
  - 覆盖 ssh 有配置 → 返回 `SSHTransport`
  - 文件范围：`tests/test_transport.py`（新建）

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含覆盖 `zsiga/transport.py` 全部公开 API 的单元测试
- 使用 `unittest.mock.patch` 隔离 `subprocess.run`、`tempfile.mktemp` 等外部依赖
- 确保所有测试可独立运行，不依赖 SSH 环境或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `tests/conftest*.py` 或其他现有测试文件
- 不添加集成测试或端到端测试
- 不修改 `pyproject.toml`、`requirements.txt` 等配置文件

### 依赖的外部条件
- `zsiga/transport.py` 保持当前 API 不变（96 行，3 类 + 1 工厂函数）
- pytest 和 unittest.mock 可用（项目已有 pytest 依赖）
- `subprocess.run`、`tempfile.mktemp` 可通过 mock 隔离

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且通过 ruff lint（0 错误）
2. 文件包含 `test_create_transport` 函数（BAC-02）
3. 文件包含覆盖所有 4 个公开组件的 `def test_` 函数，总数 ≥ 10（基类 2 + LocalTransport 3 + SSHTransport 6 + 工厂 3）
4. `python -m pytest tests/test_transport.py` 退出码 0（BAC-04）
5. 现有测试套件不受影响（`python -m pytest tests/ -x --timeout=60` 仍通过）

### 验收方式
- `ls tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` 确认测试函数数量
- `python -m pytest tests/test_transport.py -v` 确认全部通过
- `python -m ruff check tests/test_transport.py` 确认无 lint 错误
- 全量测试回归：`python -m pytest tests/ -x --timeout=60` 确认无破坏

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析，不修改）
- `tests/conftest*.py`（不修改现有 conftest）
- `pyproject.toml`、`requirements.txt`（不添加依赖）

### 项目部署分支
- deploy

### 已知风险
- **历史空转风险**：此 proposal 在 archive/skipped 中已出现 20+ 次，全部未落地。属于 auto-generated loop 模式。必须确保本次产出高质量、一次性通过的测试文件，避免再次空转。
- **SSH 环境依赖**：`SSHTransport` 测试必须完全 mock `subprocess.run`，不能依赖真实 SSH 连接
- **subprocess mock 精度**：需准确模拟 `CompletedProcess` 的 `returncode`/`stdout`/`stderr` 属性，以及 `TimeoutExpired`/`OSError` 异常路径

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（基于 archived blueprints 估算：4 个蓝本文件共 ~450 行测试代码）
