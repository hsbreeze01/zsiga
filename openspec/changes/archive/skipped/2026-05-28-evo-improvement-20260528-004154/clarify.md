# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数，3 个类）添加单元测试覆盖。模块包含抽象基类 `Transport`、本地实现 `LocalTransport`（subprocess.run）、SSH 实现 `SSHTransport`（ControlMaster 复用连接）以及工厂函数 `create_transport`。当前零测试覆盖。

### 拆解后的子任务

- [ ] 1. **Transport 基类与 LocalTransport 测试** — 验证 `Transport` 抽象接口抛 `NotImplementedError`；验证 `LocalTransport.run_shell` 正确封装 `subprocess.run` 返回 `{"exit_code", "stdout", "stderr"}`；验证 `LocalTransport.close()` 无副作用 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. **SSHTransport 测试** — 验证 `__init__` 属性赋值（host/user/port/key_path）；验证 `_base_args` 构造正确的 SSH 参数列表；验证 `_target` 返回 `user@host` 格式；验证 `_ensure_control` 调用 ssh ControlMaster 建立；验证 `run_shell` 通过 SSH 执行远程命令并返回结构化结果；验证 `close` 关闭 ControlMaster 连接；需要 mock `subprocess.run` 隔离真实 SSH 调用 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 3. **create_transport 工厂函数测试** — 验证传入含 `ssh` 配置的 `TargetConfig` 返回 `SSHTransport` 实例；验证传入无 `ssh` 配置的 `TargetConfig` 返回 `LocalTransport` 实例；验证实例属性与传入配置一致 (预估复杂度：低, 预估 token：~2000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 Transport/LocalTransport/SSHTransport/create_transport
- 使用 `unittest.mock`（mock subprocess.run）隔离外部依赖
- 测试可独立运行，不依赖 SSH 环境或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/config.py` 或其他模块
- 不涉及集成测试或端到端 SSH 连接测试
- 不修改 conftest 或其他测试基础设施

### 依赖的外部条件
- `zsiga/transport.py` 模块结构稳定（当前 96 行，无 lint 问题）
- `unittest.mock` 标准库可用
- `subprocess.run` 可被 mock 替换
- 项目 pytest 基础设施正常（conftest_zsiga.py）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 `test_create_transport` 函数
2. 至少包含覆盖三个功能模块（基类+Local、SSH、工厂）的 test 函数
3. `python -m pytest tests/test_transport.py` 退出码 0，无 ruff lint 错误
4. 每个测试可独立运行，通过 mock 隔离 subprocess，不发起真实 SSH 连接

### 验收方式
- BAC-01: `test -f tests/test_transport.py`（文件存在）
- BAC-02: `grep -q 'def test_create_transport' tests/test_transport.py`（函数存在）
- BAC-03: `grep -c 'def test_' tests/test_transport.py` 返回 ≥ 1
- BAC-04: `python -m pytest tests/test_transport.py -x` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`
- `zsiga/config.py`
- `tests/conftest_zsiga.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- main（基于 git feature branch 工作流）

### 已知风险
- SSHTransport 内部调用 `subprocess.run` 执行真实 SSH 命令，测试中必须严格 mock 防止误触发真实 SSH 连接
- `SSHTransport._ensure_control` 涉及文件系统路径（ControlMaster socket），测试需使用 `tmp_path` 或 mock 避免污染系统
- `create_transport` 依赖 `TargetConfig` 数据类构造，需确保 mock 对象的属性结构与真实 `TargetConfig` 一致

### 预估 token 消耗
- prompt: ~4000
- completion: ~5000
- 数据来源: 无历史参考（项目无同类 transport 测试先例，参照 test_git_ops.py 等类似 mock 风格测试文件规模估算）
