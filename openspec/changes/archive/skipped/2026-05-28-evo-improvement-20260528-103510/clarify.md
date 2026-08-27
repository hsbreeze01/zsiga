# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 + 3 个类：`Transport` 基类、`LocalTransport`、`SSHTransport`）创建独立单元测试文件 `tests/test_transport.py`，覆盖公开 API 和关键行为路径。

### 拆解后的子任务

- [ ] 1. **Transport 基类与工厂函数测试**（预估复杂度：低，预估 token：~2000）
  - 文件范围：`tests/test_transport.py`（新建）
  - 覆盖：`create_transport(target_config)` 工厂函数 — 本地配置返回 `LocalTransport`，SSH 配置返回 `SSHTransport`；`Transport` 基类抽象接口验证（不可直接实例化调用）
  - 验证点：BAC-02 `test_create_transport` 存在

- [ ] 2. **LocalTransport 单元测试**（预估复杂度：低，预估 token：~1500）
  - 文件范围：`tests/test_transport.py`（同上）
  - 覆盖：`LocalTransport.run_shell` 正确调用 `subprocess.run` 并返回 `{exit_code, stdout, stderr}` 结构；`close` 为空操作不报错
  - 隔离：mock `subprocess.run`，不依赖真实 shell 命令

- [ ] 3. **SSHTransport 单元测试**（预估复杂度：中，预估 token：~3000）
  - 文件范围：`tests/test_transport.py`（同上）
  - 覆盖：`SSHTransport.__init__` 参数存储；`_base_args`/`_target` 路径构造；`_ensure_control` SSH 多路复用控制通道建立；`run_shell` 通过 SSH 执行命令并解析输出；`close` 关闭控制通道
  - 隔离：mock `subprocess.run`（SSH 命令不发起真实连接）；用 `tmp_path` 或固定 fixture 替代 socket 路径

- [ ] 4. **pytest 通过验证**（预估复杂度：低，预估 token：~500）
  - 确认 `pytest tests/test_transport.py` 退出码 0，无 import 错误或 fixture 冲突
  - 验证点：BAC-04

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含所有测试类和函数
- 覆盖 `create_transport`、`LocalTransport`、`SSHTransport` 的公开方法
- 使用 mock 隔离 subprocess 调用，测试不依赖真实 SSH 或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改任何其他现有测试文件
- 不修改 `conftest_zsiga.py` 或其他 conftest 文件
- 不测试其他模块对 transport 的间接使用

### 依赖的外部条件
- `zsiga/transport.py` 模块可正常 import（无缺失依赖）
- `pytest` 和 `unittest.mock` 可用（项目已使用 pytest 框架）
- 项目中已有 transport mock 模式可参考：`test_git_ops.py` 的 `_mock_transport()`、`test_diagnoser.py` 的 `_FakeTransport`

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 `test_create_transport` 函数
2. 至少覆盖 `create_transport` 工厂路由、`LocalTransport.run_shell`、`SSHTransport.run_shell` 三个核心行为
3. `python -m pytest tests/test_transport.py` 退出码 0
4. 全部测试通过 ruff lint（无 E/F 级错误）

### 验收方式
- BAC-01：`tests/test_transport.py` 文件存在 → `test -f` 检查
- BAC-02：grep `test_create_transport` 命中 → 符号存在性检查
- BAC-03：`grep -c 'def test_' tests/test_transport.py` ≥ 1 → 计数检查
- BAC-04：`python -m pytest tests/test_transport.py` 退出码 0 → pytest 执行

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- 所有现有 `tests/test_*.py` 文件
- `tests/conftest_zsiga.py`
- `pyproject.toml`、`requirements.txt`、`zsiga.yaml`

### 项目部署分支
- main

### 已知风险
- `SSHTransport._ensure_control` 依赖 `subprocess.run` 调用真实 `ssh` 命令，测试必须彻底 mock subprocess 层，否则在无 SSH 环境下会失败
- `SSHTransport` 构造时涉及 socket 文件路径（`~/.ssh/`），测试需用 `tmp_path` 或 mock `pathlib.Path.home()` 避免污染用户环境
- 此 proposal 由自演进引擎生成，历史上同类 auto-generated 测试 proposal 有重复覆盖已有测试的风险——但经确认 `tests/test_transport.py` 确实不存在，核心前提成立

### 预估 token 消耗
- prompt: ~5000
- completion: ~3000
- 数据来源: 模块仅 96 行 + 3 类 + 1 函数，属小型测试任务；参考项目中类似规模的 `test_phase_duration.py`（241 行）和 `test_daemon_state.py`（242 行）
