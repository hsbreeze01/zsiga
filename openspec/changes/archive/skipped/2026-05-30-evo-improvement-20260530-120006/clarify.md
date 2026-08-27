# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，4 个公开符号）编写单元测试文件 `tests/test_transport.py`，覆盖 `Transport` 基类、`LocalTransport`、`SSHTransport`、`create_transport()` 工厂函数的核心行为路径。不修改源码。

### 拆解后的子任务

- [ ] 1. Transport 基类 + LocalTransport 测试 (预估复杂度：低, 预估 token：~3000)
  - 验证 `Transport` 是抽象基类，`run_shell()` 抛 `NotImplementedError`，`close()` 无操作
  - 验证 `LocalTransport.run_shell()` 调用 `subprocess.run` 并返回结果（mock subprocess）
  - 验证 `LocalTransport.close()` 无异常

- [ ] 2. SSHTransport 测试 (预估复杂度：中, 预估 token：~5000)
  - 验证 `__init__` 正确存储 ssh 配置（host/user/key）
  - 验证 `_ensure_control` 通过 subprocess 建立 ControlMaster（mock subprocess）
  - 验证 `_base_args` 返回正确的 SSH 参数列表
  - 验证 `_target` 属性返回 `user@host` 格式
  - 验证 `run_shell` 正常执行路径（mock subprocess，含超时/异常处理分支）
  - 验证 `close` 终止 ControlMaster 连接

- [ ] 3. create_transport 工厂函数测试 (预估复杂度：低, 预估 token：~2000)
  - ssh 配置存在时返回 `SSHTransport` 实例
  - ssh 配置不存在时返回 `LocalTransport` 实例
  - 验证返回类型与参数传递

- [ ] 4. 测试通过 pytest + ruff 验证 (预估复杂度：低, 预估 token：~1000)
  - `python -m pytest tests/test_transport.py` 退出码 0
  - `ruff check tests/test_transport.py` 无错误

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 4 个公开符号的核心行为
- 使用 `unittest.mock.patch` 隔离 subprocess 调用
- 使用 `pytest` fixture 提供测试数据（mock config 对象）

### OUT of scope
- 修改 `zsiga/transport.py` 源码
- 修改其他测试文件或项目配置
- 覆盖私有方法内部实现细节（仅通过公开接口验证）

### 依赖的外部条件
- `zsiga/transport.py` 源码不变（仅读取）
- 项目已有 `pytest` + `unittest.mock` 可用
- `ruff` 作为 lint 工具可用

## 目标

### 成功标准
1. 文件 `tests/test_transport.py` 存在于项目 tests/ 目录
2. 包含 `test_create_transport` 函数及其他覆盖 Transport/LocalTransport/SSHTransport 的 test_ 函数
3. 至少 1 个 `def test_` 函数（实际预期 ≥ 6 个）
4. `python -m pytest tests/test_transport.py` 退出码 0
5. `ruff check tests/test_transport.py` 无错误

### 验收方式
- 文件存在性：`test -f tests/test_transport.py`
- 函数存在性：`grep -c 'def test_' tests/test_transport.py` ≥ 1
- pytest 通过：`python -m pytest tests/test_transport.py` exit 0
- lint 通过：`ruff check tests/test_transport.py` exit 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/` 目录下所有现有测试文件
- `pyproject.toml`、`requirements.txt` 等项目配置

### 项目部署分支
- deploy

### 已知风险
- 此 proposal 历史上有 20+ 次未落地记录（全部 skipped），需确保本轮执行完成
- SSHTransport 依赖 subprocess 调用，需完整 mock 以避免真实 SSH 连接
- `create_transport` 依赖 `target_config` 对象结构，需用 mock/NamedTuple 模拟

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类 proposal 从未成功执行）
