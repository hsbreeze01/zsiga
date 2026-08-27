# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 `create_transport`，3 个类 `Transport`/`LocalTransport`/`SSHTransport`）添加单元测试文件 `tests/test_transport.py`，覆盖公开 API，使用 mock 隔离外部依赖（subprocess、SSH），不修改源码。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + create_transport 工厂函数测试** — 验证 `Transport` 抽象接口（`run_shell`/`close` 默认行为或 abstractmethod），验证 `create_transport(target_config)` 根据 transport 类型返回正确实例（local → `LocalTransport`，ssh → `SSHTransport`），覆盖无效类型边界。预估复杂度：低, 预估 token：~3000 / 无历史参考
- [ ] 2. **LocalTransport 测试** — 验证 `LocalTransport.run_shell` 正确调用 subprocess 执行本地命令、处理返回码/stdout/stderr。使用 mock 隔离 subprocess。预估复杂度：低, 预估 token：~2000 / 无历史参考
- [ ] 3. **SSHTransport 测试** — 验证 `__init__` 从配置提取 SSH 参数、`_ensure_control` 建立控制路径、`_base_args`/`_target` 组装 ssh 命令参数、`run_shell` 通过 SSH 执行远程命令、`close` 清理控制路径。使用 mock 隔离 subprocess 和文件系统操作。预估复杂度：中, 预估 token：~5000 / 无历史参考

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含对 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的单元测试
- 使用 mock 隔离 subprocess / SSH / 文件 I/O 外部依赖
- 测试可独立运行，不依赖运行时环境

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不涉及 transport 层以外的模块（config、daemon、pipeline 等）
- 不做集成测试或端到端测试

### 依赖的外部条件
- `zsiga/transport.py` 源码结构稳定（3 类 1 函数）
- 项目测试基础设施可用（pytest、unittest.mock）

## 目标

### 成功标准
1. `tests/test_transport.py` 存在且包含 `test_create_transport` 及其他 `def test_` 函数
2. 所有测试覆盖 `Transport`（基类行为）、`LocalTransport`（本地执行）、`SSHTransport`（SSH 连接与执行）、`create_transport`（工厂路由）
3. `python -m pytest tests/test_transport.py` 退出码为 0
4. `ruff check tests/test_transport.py` 无错误

### 验收方式
- `test -f tests/test_transport.py` 文件存在
- `grep -c 'def test_' tests/test_transport.py` 计数 ≥ 6（基类 1 + 工厂 2 + local 1 + ssh 3+）
- `python -m pytest tests/test_transport.py -v` 全部通过
- `ruff check tests/test_transport.py` 通过

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析，不修改）
- 项目中其他已有测试文件

### 项目部署分支
- deploy（根据 zsiga.yaml targets.zsiga.deploy_branch）

### 已知风险
- SSHTransport 涉及 subprocess 调用和文件系统操作（ControlPath），需确保 mock 充分隔离，否则测试可能因环境差异失败
- `create_transport` 的 target_config 数据结构需从源码推断，字段可能变化

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（基于模块规模 96 行 × 3 类 1 函数估算）
