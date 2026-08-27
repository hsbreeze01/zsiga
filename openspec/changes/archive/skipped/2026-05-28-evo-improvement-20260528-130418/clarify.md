# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 个类 + 1 个工厂函数）新增 `tests/test_transport.py` 单元测试文件，覆盖公开接口。

### 拆解后的子任务

- [ ] 1. **Transport 抽象基类 + LocalTransport 测试**（预估复杂度：低, 预估 token：~3000）
  - 验证 `Transport` 是抽象基类（`run_shell` / `close` 为抽象方法）
  - 测试 `LocalTransport.run_shell()` 调用 `subprocess.run` 并返回结果（mock subprocess）
  - 测试 `LocalTransport.close()` 为空操作
  - 文件范围：`tests/test_transport.py` 新建

- [ ] 2. **SSHTransport 全方法测试**（预估复杂度：中, 预估 token：~5000）
  - `__init__`：参数解析（host/port/user/key_path/control_path）
  - `_ensure_control`：建立 SSH control master（mock subprocess 调用验证）
  - `_base_args`：SSH 参数拼接正确性
  - `_target`：`user@host` 格式化
  - `run_shell`：通过 SSH 执行远程命令（验证完整调用链）
  - `close`：关闭 control master 连接
  - 需 mock `subprocess.run` 和文件系统操作
  - 文件范围：`tests/test_transport.py`（续写）

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~2000）
  - 无 `ssh_host` 的 config → 返回 `LocalTransport` 实例
  - 有 `ssh_host` 的 config → 返回 `SSHTransport` 实例
  - 验证返回类型和参数传递
  - 文件范围：`tests/test_transport.py`（续写）

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含对 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的单元测试
- 使用 mock 隔离 `subprocess.run`、文件 I/O 等外部依赖
- 确保每个测试可独立运行，不依赖 SSH 环境或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改其他测试文件或项目配置
- 不添加集成测试（真实 SSH 连接等）

### 依赖的外部条件
- `zsiga/transport.py` 可正常导入，无语法错误
- pytest 框架可用（`tests/conftest_zsiga.py` 已存在）
- 项目中已有 transport mock 模式可参考（`harness/conftest.py` 的 `MockTransport`、`test_git_ops.py` 的 `_mock_transport()`）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 `test_create_transport` 函数
2. 文件中至少包含 1 个 `def test_` 函数
3. `python -m pytest tests/test_transport.py` 退出码 0，全部测试通过
4. 测试覆盖 `Transport`（抽象基类）、`LocalTransport`（本地执行）、`SSHTransport`（SSH 远程执行全部 6 个方法）、`create_transport`（工厂函数）四个公开接口
5. 代码通过 `ruff check` 无 lint 错误

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` 确认测试函数数量 ≥ 1
- `grep 'test_create_transport' tests/test_transport.py` 确认关键测试存在
- `python -m pytest tests/test_transport.py -v` 退出码 0
- `ruff check tests/test_transport.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/conftest_zsiga.py`
- `pyproject.toml`、`requirements.txt`
- 其他已有测试文件

### 项目部署分支
- main

### 已知风险
- `SSHTransport._ensure_control` 涉及文件系统操作（创建 control path 目录），需 mock `subprocess.run` 和 `os.makedirs` 或 `pathlib.Path.mkdir`
- `SSHTransport` 的 control master 生命周期管理（init → ensure → run → close）需注意 mock 状态链的正确性
- 此 proposal 由自演进引擎生成，静态分析数据需与源码实际内容交叉验证

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（transport 模块此前无测试），按模块规模（96 行）估算
