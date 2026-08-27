# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试覆盖的 `zsiga/transport.py`（96 行，3 个类 + 1 个工厂函数）创建单元测试文件 `tests/test_transport.py`。模块包含抽象基类 `Transport`、本地执行 `LocalTransport`（subprocess.run）、SSH 远程执行 `SSHTransport`（ControlMaster 管理、超时/异常处理）、以及工厂函数 `create_transport()`。不修改源码。

### 拆解后的子任务
- [ ] 1. 测试基类 Transport 与 LocalTransport（预估复杂度：低, 预估 token：~3000 / 无历史参考）
  - 验证 `Transport` 是抽象基类，`run_shell` 抛 `NotImplementedError`，`close` 为 no-op
  - 验证 `LocalTransport.run_shell` 正确调用 `subprocess.run` 并返回结果
  - 验证 `LocalTransport.run_shell` 在命令失败时传播 `subprocess.CalledProcessError`
  - Mock: `subprocess.run`
  - 涉及文件: `tests/test_transport.py`（新建）

- [ ] 2. 测试 SSHTransport 核心行为（预估复杂度：中, 预估 token：~5000 / 无历史参考）
  - 验证 `__init__` 正确解析 ssh 配置（host/port/user/key_path）并存储
  - 验证 `_ensure_control` 调用 subprocess 建立 ControlMaster socket
  - 验证 `_base_args` 返回正确的 SSH 参数列表（含 ControlMaster/ControlPath）
  - 验证 `_target` 生成 `[user@]host` 格式字符串
  - 验证 `run_shell` 通过 SSH 执行命令并返回输出
  - 验证 `run_shell` 超时场景抛出预期异常
  - 验证 `close` 正确关闭 ControlMaster 连接
  - Mock: `subprocess.run`、`os.path.exists`、`pathlib.Path`
  - 涉及文件: `tests/test_transport.py`

- [ ] 3. 测试 create_transport 工厂函数（预估复杂度：低, 预估 token：~2000 / 无历史参考）
  - 验证 `target_config.ssh` 为 None/空时返回 `LocalTransport` 实例
  - 验证 `target_config.ssh` 有值时返回 `SSHTransport` 实例
  - 验证 `SSHTransport` 构造参数正确传递（host/port/user/key_path）
  - 涉及文件: `tests/test_transport.py`

## 边界

### IN scope
- 创建 `tests/test_transport.py`，覆盖 Transport、LocalTransport、SSHTransport、create_transport
- 使用 unittest.mock 隔离 subprocess、文件系统等外部依赖
- 每个测试独立运行，不依赖运行时 SSH 环境

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/config.py` 中 target_config 的定义
- 不涉及 transport.py 的调用方（pipeline/git_ops 等）的测试
- 不添加集成测试或端到端测试

### 依赖的外部条件
- `zsiga/transport.py` 可正常导入且接口稳定
- `unittest.mock`（标准库，无额外依赖）
- `unittest.mock.MagicMock` 用于模拟 `target_config` 对象（需含 `.ssh` 属性）

## 目标

### 成功标准
1. `tests/test_transport.py` 存在且包含 `test_create_transport` 函数
2. 测试文件覆盖全部 3 个类（Transport/LocalTransport/SSHTransport）和工厂函数的核心行为
3. `python -m pytest tests/test_transport.py` 退出码 0，全部测试通过
4. 所有外部依赖通过 mock 隔离，无网络/SSH/文件系统副作用

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在（BAC-01）
- `grep -c 'def test_' tests/test_transport.py` 返回 ≥ 1（BAC-03）
- `grep 'test_create_transport' tests/test_transport.py` 确认存在（BAC-02）
- `python -m pytest tests/test_transport.py -v` 退出码 0（BAC-04）
- `python -m ruff check tests/test_transport.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `zsiga/config.py`
- 任何现有测试文件

### 项目部署分支
- deploy（zsiga 目标项目默认分支）

### 已知风险
- SSHTransport 依赖 ControlMaster socket 文件路径（`~/.ssh/` 下），需确保 mock 彻底避免真实文件操作
- `target_config` 不是 dataclass/TypedDict，而是由 config 加载的动态对象，mock 时需用 MagicMock 或 SimpleNamespace 模拟 `.ssh` 属性
- `create_transport` 内部直接构造 SSHTransport（传入 `target_config.ssh`），需确保 mock 的 ssh 属性结构与源码期望一致

### 预估 token 消耗
- prompt: ~4000
- completion: ~4000
- 数据来源: 无历史参考（基于 transport.py 96 行、预计测试代码 ~120-180 行估算）
