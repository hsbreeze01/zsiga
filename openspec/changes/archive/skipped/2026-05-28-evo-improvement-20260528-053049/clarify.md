# clarify.md — add-tests-transport

## 需求拆解
### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 类 + 1 工厂函数）新建 `tests/test_transport.py`，覆盖 `Transport` 基类、`LocalTransport`、`SSHTransport`、`create_transport` 的公开行为，不修改源码。

### 拆解后的子任务
- [ ] 1. **Transport 基类 + LocalTransport 测试**（预估复杂度：低, 预估 token：~2000）
  - 验证 `Transport` 是抽象基类，`run_shell()` 抛 `NotImplementedError`，`close()` 无副作用
  - 验证 `LocalTransport.run_shell()` 正确调用 `subprocess.run` 并返回结果
  - 使用 `unittest.mock.patch` 隔离 `subprocess.run`
  - 文件范围：`tests/test_transport.py` 新建

- [ ] 2. **SSHTransport 核心行为测试**（预估复杂度：中, 预估 token：~3500）
  - 验证 `__init__` 正确存储 SSH 配置（host/user/key）
  - 验证 `_base_args()` 返回正确的 ssh 参数列表
  - 验证 `_target()` 格式化远程目标路径
  - 验证 `_ensure_control()` 控制通道建立逻辑（mock subprocess）
  - 验证 `run_shell()` 通过 SSH 执行命令并返回结果
  - 验证 `close()` 关闭控制通道（如存在）
  - 全程 mock `subprocess.run`，不触发真实 SSH 连接
  - 文件范围：`tests/test_transport.py`（追加）

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~1500）
  - 验证无 `ssh` 配置时返回 `LocalTransport` 实例
  - 验证有 `ssh` 配置时返回 `SSHTransport` 实例
  - 验证返回类型的正确性（`isinstance` 检查）
  - 文件范围：`tests/test_transport.py`（追加）

- [ ] 4. **pytest + ruff 验证通过**（预估复杂度：低, 预估 token：~500）
  - `python -m pytest tests/test_transport.py` 退出码 0
  - `ruff check tests/test_transport.py` 无错误
  - 文件范围：`tests/test_transport.py`

## 边界
### IN scope
- 新建 `tests/test_transport.py`，覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport`
- 使用 `unittest.mock` 隔离 `subprocess.run` 调用
- 参考项目已有 mock transport 模式（`conftest_zsiga.py` 中 `_MockTransport`、`test_diagnoser.py` 中 `_FakeTransport`）

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改其他已有测试文件
- 不修改 `conftest_zsiga.py`
- 不涉及 SSH 集成测试（仅单元测试 + mock）

### 依赖的外部条件
- `zsiga/transport.py` 保持当前结构不变（3 类 + 1 工厂函数）
- 项目 pytest 基础设施可用（`conftest_zsiga.py`、`pyproject.toml`）
- `unittest.mock` 可用（Python 标准库，无需额外依赖）

## 目标
### 成功标准
1. `tests/test_transport.py` 文件存在且包含至少 6 个 `def test_` 函数
2. 文件中包含 `test_create_transport` 函数（BAC-02）
3. 覆盖 `Transport.run_shell`（NotImplementedError）、`Transport.close`（no-op）
4. 覆盖 `LocalTransport.run_shell`（mock subprocess.run）
5. 覆盖 `SSHTransport.__init__`、`_base_args`、`_target`、`run_shell`、`close`
6. 覆盖 `create_transport` 的 local/ssh 两条分支
7. `python -m pytest tests/test_transport.py` 退出码 0（BAC-04）
8. `ruff check tests/test_transport.py` 无错误

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` ≥ 6
- `grep 'def test_create_transport' tests/test_transport.py` 命中
- `python -m pytest tests/test_transport.py -v` 全部 PASSED
- `ruff check tests/test_transport.py` 退出码 0

## 约束
### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/conftest_zsiga.py`
- 所有其他已有测试文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- main

### 已知风险
- `SSHTransport._ensure_control` 可能涉及控制通道文件创建，mock 不完整可能导致测试意外触碰本地文件系统 → 用 `tmp_path` 或 mock `subprocess.run` 完全隔离
- 项目中已有 `_MockTransport`（conftest_zsiga.py）和 `_FakeTransport`（test_diagnoser.py），测试中应避免命名冲突 → 使用唯一类名（如 `TestTransportBase`、`TestLocalTransport`、`TestSSHTransport`、`TestCreateTransport`）
- 自演进引擎生成的 proposal 曾有 BAC 形同虚设的问题（BAC-03 仅要求 ≥1 个 test），本 clarify 将标准提升到 ≥6 以确保实质覆盖

### 预估 token 消耗
- prompt: ~3000
- completion: ~4000
- 数据来源: 无历史参考（transport.py 尚无测试），参考同类 test 文件规模（`test_diagnoser.py` ~120 行）
