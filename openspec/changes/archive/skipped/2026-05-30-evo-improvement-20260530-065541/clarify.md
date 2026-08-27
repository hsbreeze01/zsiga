# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 + 3 个类）编写单元测试文件 `tests/test_transport.py`，覆盖公开接口。

### 拆解后的子任务
- [ ] 1. **Transport 基类 + LocalTransport 测试** — 验证 `Transport` 抽象接口（`run_shell`, `close`）和 `LocalTransport.run_shell` 通过 `subprocess.run` 执行本地命令，使用 mock 隔离 subprocess（预估复杂度：低, 预估 token：~3000）
- [ ] 2. **SSHTransport 测试** — 验证 `SSHTransport.__init__`、`_ensure_control`、`_base_args`、`_target`、`run_shell`、`close` 六个方法，覆盖 SSH 控制路径创建、参数拼接、远程命令执行、连接关闭等路径，mock subprocess 和文件系统操作（预估复杂度：中, 预估 token：~5000）
- [ ] 3. **create_transport 工厂函数测试** — 验证 `create_transport(target_config)` 根据 target_config 中的传输类型正确返回 `LocalTransport` 或 `SSHTransport` 实例，覆盖 local/ssh 两种分支及边界情况（预估复杂度：低, 预估 token：~2000）

## 边界

### IN scope
- 新建 `tests/test_transport.py`
- 覆盖 `Transport` 基类接口、`LocalTransport`、`SSHTransport`（含所有公开方法）、`create_transport` 工厂函数
- 使用 mock 隔离 subprocess / 文件系统等外部依赖

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `tests/conftest_zsiga.py` 或其他现有测试文件
- 不涉及集成测试或端到端 SSH 连接测试

### 依赖的外部条件
- `zsiga/transport.py` 导出的 `Transport`, `LocalTransport`, `SSHTransport`, `create_transport` 符号保持稳定
- `tests/conftest_zsiga.py` 中已有 `mock_transport` fixture 可参考但非必需
- pytest + unittest.mock 可用（项目已有依赖）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 `test_create_transport` 函数
2. 文件中至少包含 3 个 `def test_` 函数（覆盖 LocalTransport / SSHTransport / create_transport 三组）
3. `python -m pytest tests/test_transport.py` 退出码为 0，无 skip/fail
4. 所有测试使用 mock 隔离，不依赖真实 SSH 连接或外部进程

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` ≥ 3
- `python -m pytest tests/test_transport.py -v` 全部 PASSED
- `ruff check tests/test_transport.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`
- `tests/conftest_zsiga.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- deploy

### 已知风险
- **历史循环风险**：同名 proposal 已被提交 12+ 次均在 proposal 阶段被 skip/archive，需确保本轮真正产出可合并的测试文件而非再次空转
- **现有参考实现**：`openspec/changes/` 下已有多套归档的 test_transport 实现可参考，但均为长命名格式（`test_spec_evo_*`），本轮应使用 `tests/test_transport.py` 标准命名
- **conftest 冲突**：`tests/conftest_zsiga.py` 中已有 `mock_transport` fixture，新测试需避免命名冲突

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同名 proposal 均未执行到实现阶段）
