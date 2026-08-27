# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 工厂函数 `create_transport`，3 个类 `Transport`/`LocalTransport`/`SSHTransport`）添加单元测试覆盖。模块当前 ruff lint 零问题，平均圈复杂度 2.0，无高 CC 函数。测试需使用 mock 隔离 subprocess 等外部依赖，确保可独立运行。

### 拆解后的子任务
- [ ] 1. **Transport 抽象基类与 LocalTransport 测试**（预估复杂度：低, 预估 token：~3000）
  - 验证 `Transport.run_shell()` 抛出 `NotImplementedError`
  - 验证 `Transport.close()` 为空操作（不抛异常）
  - 验证 `LocalTransport.run_shell()` 正确调用 `subprocess.run` 并返回 `{"exit_code", "stdout", "stderr"}` 字典结构
  - 覆盖 `cwd`/`timeout`/`stdin_data` 参数传递路径
  - 覆盖 subprocess 异常路径（`TimeoutExpired` 等）
  - 文件范围：`tests/test_transport.py`（新建），读取 `zsiga/transport.py`

- [ ] 2. **SSHTransport 测试**（预估复杂度：中, 预估 token：~4000）
  - 验证 `SSHTransport.__init__` 正确存储 `host`/`user`/`port`/`key_path` 参数
  - 验证 `_target()` 返回正确的 `[user@]host` 格式
  - 验证 `_base_args()` 返回正确的 ssh 参数列表
  - 验证 `_ensure_control()` 建立 ControlMaster（mock subprocess）
  - 验证 `run_shell()` 正确组装 ssh 命令并处理超时/异常
  - 验证 `close()` 关闭 ControlMaster socket
  - 文件范围：`tests/test_transport.py`，读取 `zsiga/transport.py`

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~2000）
  - 验证 `ssh` 为 `None` 时返回 `LocalTransport` 实例
  - 验证 `ssh` 存在时返回 `SSHTransport` 实例且参数正确传递（`host`/`user`/`port`/`key_path`）
  - 需构造 `TargetConfig`/`SSHConfig` mock 对象（来自 `zsiga/config.py`）
  - 文件范围：`tests/test_transport.py`，读取 `zsiga/transport.py`、`zsiga/config.py`

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含 Transport/LocalTransport/SSHTransport/create_transport 的单元测试
- 使用 `unittest.mock`（mock/subprocess）隔离外部依赖
- 测试需通过 `pytest` 退出码 0

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/config.py` 或其他已有文件
- 不修改 `pyproject.toml`、`requirements.txt` 等配置文件
- 不涉及集成测试（不实际连接 SSH）

### 依赖的外部条件
- `zsiga/transport.py` 当前 API 稳定（96 行，3 类 1 函数）
- `zsiga/config.py` 中 `TargetConfig`/`SSHConfig` 数据类定义稳定
- 项目已安装 `pytest`、`unittest.mock`（标准库）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 `test_create_transport` 函数
2. 至少覆盖 3 个类的核心方法（`run_shell`、`close`、`__init__`）和 `create_transport` 工厂函数
3. `python -m pytest tests/test_transport.py` 退出码 0，无 skip/error
4. ruff lint 对新测试文件零报错

### 验收方式
- 运行 `python -m pytest tests/test_transport.py -v` 确认全部通过
- 运行 `ruff check tests/test_transport.py` 确认零 lint 问题
- 检查测试函数数量 ≥ 4（对应 BAC-03 的"至少 1 个"，实际应覆盖全部公开 API）

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析，不修改）
- `zsiga/config.py`
- `pyproject.toml`
- `requirements.txt`
- 所有已有测试文件

### 项目部署分支
- deploy

### 已知风险
- **循环 proposal 风险**：此 proposal 已在 archive 中出现 20+ 次均被 skip，根因是自演进引擎的循环生成问题。执行时需确保一次性交付成功，避免产生新的 skip archive
- **SSHConfig/TargetConfig 构造**：测试需要 mock 或直接实例化 `zsiga/config.py` 中的数据类，需确认这些类可直接导入且构造函数签名稳定
- **SSHTransport 的 ControlMaster**：依赖 `tempfile.mktemp()` 和 subprocess 调用真实 `ssh` 命令，测试中必须完全 mock subprocess

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考（此前 20+ 轮均在 gate 阶段被拦截，从未进入执行阶段）
