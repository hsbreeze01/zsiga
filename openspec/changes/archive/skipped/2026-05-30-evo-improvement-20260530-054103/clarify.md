# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，3 类 1 工厂函数）添加单元测试文件 `tests/test_transport.py`，覆盖公开接口（`Transport` 抽象基类、`LocalTransport`、`SSHTransport`、`create_transport` 工厂函数），不修改源码。

### 拆解后的子任务

- [ ] 1. **Transport 基类与 LocalTransport 测试**（预估复杂度：低，预估 token：~1500 / 无历史参考）
  - 验证 `Transport` 为抽象基类，`run_shell` / `close` 为抽象方法
  - 验证 `LocalTransport.run_shell` 调用 `subprocess.run` 并返回结果
  - 范围：`Transport` (L6-L13), `LocalTransport` (L16-L24)

- [ ] 2. **SSHTransport 完整测试**（预估复杂度：中，预估 token：~3000 / 无历史参考）
  - 验证 `__init__` 正确存储 SSH 配置并调用 `_ensure_control`
  - 验证 `_ensure_control` 在 control path 不存在时创建目录（mock `subprocess.run`）
  - 验证 `_base_args` 生成正确的 SSH 参数（含 ControlPath、端口、密钥等）
  - 验证 `_target` 拼接 `user@host` 格式
  - 验证 `run_shell` 组装完整 SSH 命令并执行
  - 验证 `close` 通过 control master 关闭连接
  - 使用 `unittest.mock` 隔离 `subprocess.run`、`os.path.exists`、`os.makedirs`
  - 范围：`SSHTransport` (L27-L83)

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低，预估 token：~1500 / 无历史参考）
  - 验证 transport=`local` 时返回 `LocalTransport` 实例
  - 验证 transport=`ssh` 时返回 `SSHTransport` 实例
  - 验证未知 transport 类型抛出预期异常
  - 范围：`create_transport` (L86-L95)

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含对 Transport / LocalTransport / SSHTransport / create_transport 的单元测试
- 使用 `unittest.mock` 隔离 subprocess、文件系统等外部依赖
- 确保所有测试可独立运行，不依赖 SSH 环境或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `tests/conftest.py` 或其他已有测试文件
- 不涉及集成测试或端到端测试

### 依赖的外部条件
- `zsiga/transport.py` 已存在且接口稳定（96 行，0 lint 问题）
- pytest 框架可用（项目已有 100+ 测试文件）
- `unittest.mock` 标准库可用

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥ 8 个 `def test_` 函数
2. 覆盖全部 3 个类的公开方法及 `create_transport` 工厂函数
3. `python -m pytest tests/test_transport.py` 退出码为 0
4. `python -m ruff check tests/test_transport.py` 无错误

### 验收方式
- BAC-01: `tests/test_transport.py` 文件存在
- BAC-02: 文件中包含 `test_create_transport` 函数
- BAC-03: 文件中包含至少 1 个 `def test_` 函数
- BAC-04: `python -m pytest tests/test_transport.py` 退出码 0
- 额外: `ruff check tests/test_transport.py` 通过

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析，不修改源码）
- 所有已有测试文件
- `conftest.py` / `pyproject.toml` / `requirements.txt`

### 项目部署分支
- deploy

### 已知风险
- SSHTransport 依赖 `paramiko` 或 `subprocess` 调用 SSH，需要 mock 隔离以避免环境依赖
- `_ensure_control` 涉及文件系统操作，需 mock `os.path.exists` / `os.makedirs`
- 同目录下已有 3 个 spec 命名测试文件（`test_spec_evo_improvement_20260530_054103__*.py`），需避免功能重复

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考（基于模块规模 96 行、CC 均值 2.0 估算）
