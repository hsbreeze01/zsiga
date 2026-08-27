# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 类 + 1 工厂函数）添加单元测试文件 `tests/test_transport.py`。该模块定义了传输抽象基类 `Transport`、本地实现 `LocalTransport`、SSH 实现 `SSHTransport` 及工厂函数 `create_transport`，当前无任何直接测试覆盖。

### 拆解后的子任务
- [ ] 1. 抽象基类 Transport + LocalTransport 测试（预估复杂度：低, 预估 token：~3000 / 无历史参考）
  - 验证 `Transport` 是抽象基类，`run_shell` 抛 `NotImplementedError`，`close` 为空操作
  - 验证 `LocalTransport.run_shell` 正确封装 `subprocess.run`（mock subprocess，断言调用参数和返回值）
  - 验证 `LocalTransport.close()` 无副作用
  - 文件范围：`tests/test_transport.py`

- [ ] 2. SSHTransport 测试（预估复杂度：中, 预估 token：~5000 / 无历史参考）
  - 验证 `__init__` 正确存储 SSH 配置（host, user, key_path, port 等）
  - 验证 `_ensure_control` 创建控制路径目录（mock `os.makedirs` / `Path.mkdir`）
  - 验证 `_base_args` 生成正确的 SSH 参数列表（含控制路径、密钥等）
  - 验证 `_target` 返回 `user@host` 格式字符串
  - 验证 `run_shell` 通过 subprocess 执行远程命令并处理超时
  - 验证 `close` 清理控制路径连接
  - 全部使用 mock 隔离 subprocess 和文件系统操作
  - 文件范围：`tests/test_transport.py`

- [ ] 3. create_transport 工厂函数测试（预估复杂度：低, 预估 token：~2000 / 无历史参考）
  - 验证无 SSH 配置时返回 `LocalTransport` 实例
  - 验证有 SSH 配置时返回 `SSHTransport` 实例
  - 验证传入的 `target_config` 参数正确传递到对应 Transport 构造函数
  - 文件范围：`tests/test_transport.py`

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 全部公开接口
- 使用 `unittest.mock` 隔离 `subprocess.run`、文件系统操作、SSH 连接等外部依赖
- 测试可独立运行，不依赖运行时环境（无真实 SSH 连接）

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `tests/conftest.py` 或其他现有测试文件
- 不测试 `zsiga/harness/conftest.py` 中的 `MockTransport`（属于 harness 层，接口不同）
- 不涉及其他模块（orchestrator、daemon 等）对 transport 的集成使用

### 依赖的外部条件
- `zsiga/transport.py` 源码在实现期间不被修改
- `pytest` 和 `unittest.mock` 可用（项目已有 pytest 依赖）
- 现有测试套件全部通过，无环境阻塞

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含至少 3 个 `def test_` 函数（覆盖 Transport 基类、LocalTransport、SSHTransport、create_transport）
2. `tests/test_transport.py` 中包含名为 `test_create_transport` 的测试函数
3. 所有测试使用 mock 隔离外部依赖，不发起真实 SSH 连接或本地子进程
4. `python -m pytest tests/test_transport.py` 退出码 0
5. `python -m pytest tests/test_transport.py` 无 skip 或 xfail

### 验收方式
- 确认 `tests/test_transport.py` 文件存在于项目根目录
- 确认文件中包含 `test_create_transport` 函数定义
- 运行 `python -m pytest tests/test_transport.py -v` 全部 PASSED
- 运行 `ruff check tests/test_transport.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/conftest.py` 及所有其他现有测试文件
- `pyproject.toml`、`requirements.txt`（不新增依赖）

### 项目部署分支
- deploy

### 已知风险
- **历史循环风险**：同类型 proposal 已有 20+ 次被 skip/pushback/archive 的记录，需避免重蹈覆辙——测试必须真实覆盖公开接口，不能是空壳或占位符
- **SSH mock 复杂度**：`SSHTransport` 涉及控制路径管理（`_ensure_control`）、超时处理等，mock 需仔细设计以避免假阳性
- **接口稳定性**：`transport.py` 96 行、结构简单，接口变更风险低

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（基于 transport.py 96 行规模 + 3 类 1 函数的复杂度估算）
