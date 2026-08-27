# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 个类，1 个工厂函数）添加单元测试文件 `tests/test_transport.py`，覆盖所有公开类和方法，使用 mock 隔离 subprocess 依赖，确保 pytest 退出码 0。

### 拆解后的子任务

- [ ] 1. **Transport 基类测试** — 验证 `Transport.run_shell()` 抛 `NotImplementedError`，`Transport.close()` 返回 `None`（预估复杂度：低，预估 token：~1500）
- [ ] 2. **LocalTransport 测试** — mock `subprocess.run`，验证 `run_shell` 正确透传 `shell=True/capture_output/text=True/cwd/timeout/stdin` 参数，验证返回值格式 `{exit_code, stdout, stderr}`（预估复杂度：低，预估 token：~2000）
- [ ] 3. **SSHTransport 测试** — mock `subprocess.run` + `tempfile.mktemp`，覆盖 `__init__` 控制路径初始化、`_ensure_control` 幂等性、`_base_args` 返回值、`_target` cwd 前缀拼接、`run_shell` 正常执行 / `TimeoutExpired` 返回 exit_code=-1 / 通用异常处理、`close` 发送 `-O exit`（预估复杂度：中，预估 token：~3000）
- [ ] 4. **create_transport 工厂函数测试** — 用 `SimpleNamespace` 构造含/不含 ssh 配置的 target_config，验证返回 `LocalTransport` 或 `SSHTransport` 实例（预估复杂度：低，预估 token：~1500）

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 Transport / LocalTransport / SSHTransport / create_transport
- 使用 `unittest.mock.patch` 隔离所有 `subprocess.run` 和 `tempfile.mktemp` 调用
- 确保每个测试可独立运行，不依赖真实网络或 SSH

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改其他测试文件或项目配置
- 不处理 transport 模块的集成测试或端到端测试

### 依赖的外部条件
- `zsiga/transport.py` 保持当前 API 不变（96 行，3 类 1 函数）
- pytest 可正常运行（项目已有 100+ 测试文件）
- `unittest.mock` 可用（标准库）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含至少 10 个 `def test_` 函数
2. 覆盖全部 4 个公开组件：Transport、LocalTransport、SSHTransport、create_transport
3. 所有 subprocess 调用通过 mock 隔离，不依赖外部环境
4. `python -m pytest tests/test_transport.py` 退出码 0
5. `ruff check tests/test_transport.py` 无错误

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c "def test_" tests/test_transport.py` 确认测试函数数量
- `python -m pytest tests/test_transport.py -v` 全部通过
- `ruff check tests/test_transport.py` 零问题

## 约束

### 不能修改的文件
- `zsiga/transport.py` — 仅读取分析，不做任何修改

### 项目部署分支
- main

### 已知风险
- **历史空转风险**：同名 proposal `add-tests-transport` 已在 archive 中出现 20+ 次，全部被 skip/archive，测试代码从未落地到 `tests/test_transport.py`。本轮必须确保文件实际写入项目 `tests/` 目录而非仅存在于 change 目录
- **循环生成风险**：若本轮再次 skip，自演进引擎将继续生成重复 proposal，消耗资源

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考（前 20+ 轮均未到达 implement 阶段）
