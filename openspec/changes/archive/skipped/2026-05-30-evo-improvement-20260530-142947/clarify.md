# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，1 工厂函数 + 3 类）添加单元测试文件 `tests/test_transport.py`。该模块是项目的命令执行抽象层（Transport ABC + LocalTransport + SSHTransport + create_transport 工厂），被 10+ 个核心模块依赖注入，但至今没有直接测试文件。

### 拆解后的子任务

- [ ] 1. **Transport 基类契约测试** — 验证 `Transport` ABC 的 `run_shell()` 抛 `NotImplementedError`，`close()` 返回 `None`（预估复杂度：低, 预估 token：~1500）
- [ ] 2. **LocalTransport 测试** — 验证 `run_shell()` 正确委托 `subprocess.run`，传递 shell/cwd/timeout/input 参数，解析返回值为 `{"exit_code", "stdout", "stderr"}` 格式；覆盖正常返回、超时、通用异常三条路径（预估复杂度：中, 预估 token：~2500）
- [ ] 3. **SSHTransport 测试** — 验证 `__init__` 参数存储与 `key_path` expanduser；`_target()` 在有/无 user 时的格式；`_base_args()` 根据 port/key_path 条件构造参数；`run_shell()` 的 cwd 前缀拼接、TimeoutExpired 和 OSError 异常处理；`close()` 的 ControlMaster 清理；`_ensure_control()` 的 ControlPath 创建（预估复杂度：中, 预估 token：~3500）
- [ ] 4. **create_transport 工厂函数测试** — 验证 `target_config.ssh` 为 None/False 时返回 `LocalTransport`，为 truthy 对象时返回 `SSHTransport` 并正确传递 host/user/port/key_path（预估复杂度：低, 预估 token：~1500）
- [ ] 5. **pytest 全量验证** — 确保 `python -m pytest tests/test_transport.py` 退出码 0，无 import 错误，所有 mock 隔离正确（预估复杂度：低, 预估 token：~500）

## 边界

### IN scope
- 创建 `tests/test_transport.py`，覆盖 Transport、LocalTransport、SSHTransport、create_transport
- 使用 `unittest.mock.patch` 隔离 subprocess 依赖
- 使用 `MagicMock` 模拟 target_config 对象
- 所有测试可独立运行，不依赖 SSH 环境或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/harness/conftest.py` 中的 `MockTransport`（用途不同，接口不匹配）
- 不修改 `zsiga/pipeline/spec_pytest_check.py` 中的 `_MockTransport`
- 不创建额外的 conftest 或 fixture 文件

### 依赖的外部条件
- `zsiga/transport.py` 模块可正常 import（无外部依赖，仅用 subprocess/tempfile/pathlib）
- pytest + unittest.mock 可用（项目已有 pytest 测试基础设施）
- 本轮 change 目录已有历史生成的测试文件可参考模式（但不直接复用，因历史文件从未通过 verify）

## 目标

### 成功标准
1. `tests/test_transport.py` 存在于项目 tests 目录下
2. 包含覆盖 4 个目标符号的测试：Transport 基类、LocalTransport、SSHTransport、create_transport
3. 测试使用 mock 隔离 subprocess，不触发真实 shell/SSH 调用
4. `python -m pytest tests/test_transport.py` 退出码 0
5. `python -m ruff check tests/test_transport.py` 无 lint 错误

### 验收方式
- 检查 `tests/test_transport.py` 文件存在
- grep 确认 `test_create_transport` 函数存在（BAC-02）
- grep 确认至少 1 个 `def test_` 函数存在（BAC-03）
- 执行 `python -m pytest tests/test_transport.py -v` 验证退出码 0（BAC-04）
- 执行 `python -m ruff check tests/test_transport.py` 验证无错误

## 约束

### 不能修改的文件
- `zsiga/transport.py` — 仅读取分析，不修改
- `zsiga/harness/conftest.py` — MockTransport 接口不同，不相关
- `tests/conftest_zsiga.py` — 不引入新 fixture
- 所有其他 `zsiga/` 源码文件

### 项目部署分支
- deploy

### 已知风险
- **循环空转风险（高）**：此 proposal 已被自演进引擎生成 27+ 次，全部 skip/pushback，0 次成功。常见失败原因是 verify 阶段 import 错误或依赖缺失。本轮必须确保测试文件中 import 路径正确（`from zsiga.transport import ...`），且 mock 隔离无遗漏
- **历史代码不可复用**：change 目录中已有 4 个历史生成的测试文件，但这些文件从未通过 verify，可能包含 import 错误或其他问题。应从零编写，仅参考其测试场景覆盖思路
- **SSHTransport 测试复杂度**：SSHTransport 有 6 个方法和 ControlMaster 多路复用逻辑，需仔细 mock subprocess.run 的多次调用（_ensure_control + run_shell），避免 mock 状态泄漏

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（27+ 次历史尝试均未成功，无有效基准数据）
