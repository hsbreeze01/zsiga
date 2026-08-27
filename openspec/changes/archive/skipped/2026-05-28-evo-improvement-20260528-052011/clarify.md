# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 个类，1 个工厂函数）创建 `tests/test_transport.py`，覆盖所有公开接口的单元测试。模块包含 `Transport` 抽象基类、`LocalTransport`（本地 subprocess）、`SSHTransport`（SSH 远程执行）、`create_transport` 工厂函数。

### 拆解后的子任务

- [ ] 1. **Transport 抽象基类合约测试**（预估复杂度：低, 预估 token：~800）
  - 验证 `Transport.run_shell()` 抛出 `NotImplementedError`
  - 验证 `Transport.close()` 返回 `None`（无操作）
  - 文件范围：`tests/test_transport.py`，涉及 `zsiga/transport.py` L6-L13

- [ ] 2. **LocalTransport Shell 执行测试**（预估复杂度：低, 预估 token：~1200）
  - Mock `subprocess.run`，验证委托调用并返回 `{exit_code, stdout, stderr}` 字典
  - 验证 `cwd` 和 `timeout` 参数正确转发
  - 验证 `stdin_data` 作为 `input` 参数转发
  - 文件范围：`tests/test_transport.py`，涉及 `zsiga/transport.py` L16-L24

- [ ] 3. **SSHTransport 初始化与内部方法测试**（预估复杂度：中, 预估 token：~2000）
  - 初始化：存储 `host/user/port/key_path`，验证 `key_path` 经 `Path.expanduser()` 展开，默认值 `user=None, port=22, key_path=None`
  - `_target` 格式：有 user → `"alice@srv"`，无 user → `"srv"`
  - `_base_args` 参数组装：默认端口无密钥（不含 `-p`/`-i`），自定义端口带密钥（含 `-p 2222` 和 `-i key_path`）
  - `_ensure_control` 控制路径：首次调用创建 control master（含 `ControlMaster=auto`），已存在时幂等不调用 `subprocess.run`
  - 文件范围：`tests/test_transport.py`，涉及 `zsiga/transport.py` L27-L83

- [ ] 4. **SSHTransport.run_shell 远程执行与 close 测试**（预估复杂度：中, 预估 token：~2000）
  - 通过 SSH 执行命令，验证 `subprocess.run` 调用参数
  - `cwd` 参数拼接为 `cd '{cwd}' && cmd`
  - `TimeoutExpired` → 返回 `exit_code=-1`
  - 通用异常 → 返回 `exit_code=-1, stderr=str(e)`
  - `close`：有 control_path → 发送 `-O exit` 并重置；无 control_path → 不调用 `subprocess.run`
  - 文件范围：`tests/test_transport.py`，涉及 `zsiga/transport.py` L27-L83

- [ ] 5. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~1000）
  - 无 ssh 属性 → 返回 `LocalTransport` 实例
  - 有 ssh 配置 → 返回 `SSHTransport` 实例
  - ssh 为 falsy（如空 dict/None）→ 返回 `LocalTransport` 实例
  - 文件范围：`tests/test_transport.py`，涉及 `zsiga/transport.py` L86-L95

## 边界

### IN scope
- 创建 `tests/test_transport.py`，覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的公开接口
- 使用 `unittest.mock` / `monkeypatch` 隔离 `subprocess.run`、`tempfile.mktemp`、`Path.expanduser()`
- 每个测试可独立运行，不依赖运行时环境（无真实 SSH 连接、无真实 subprocess 执行）

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改其他现有文件（`conftest_zsiga.py` 等）
- 不添加集成测试（需要真实 SSH 连接或真实 subprocess 的场景）
- 不测试私有方法的前缀约定（仅验证行为，不验证命名）

### 依赖的外部条件
- `zsiga/transport.py` 存在且接口稳定（96 行，无 lint 问题）
- 项目 pytest 基础设施可用（`conftest_zsiga.py` 提供 fixture 支持）
- `subprocess`、`tempfile`、`pathlib.Path` 可通过 `unittest.mock` mock

## 目标

### 成功标准
1. `tests/test_transport.py` 存在且包含 `test_create_transport` 函数
2. 文件中包含至少 1 个 `def test_` 函数（实际目标：覆盖全部 20 个规划场景）
3. `python -m pytest tests/test_transport.py` 退出码 0
4. `ruff check tests/test_transport.py` 无 lint 错误

### 验收方式
- BAC-01：检查 `tests/test_transport.py` 文件存在性
- BAC-02：检查文件中 `test_create_transport` 函数名存在（AST 或 grep 验证）
- BAC-03：统计文件中 `def test_` 函数数量 ≥ 1
- BAC-04：执行 `python -m pytest tests/test_transport.py` 验证退出码为 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析，不修改）
- `tests/conftest_zsiga.py`
- 项目中所有其他现有文件

### 项目部署分支
- main

### 已知风险
- SSHTransport 涉及 `subprocess.run` 调用 ssh 命令，mock 不精确可能导致测试与实现耦合过紧——建议通过验证返回值（而非 mock 调用次数）来降低耦合
- `_ensure_control` 依赖 `tempfile.mktemp` 生成 control path，mock 时需确保路径一致性
- 此 proposal 由自演进引擎生成，静态分析数据已验证（模块确实无测试文件、96 行、3 类 1 函数、无 lint 问题）

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（transport 模块无同类测试任务先例，参考同项目其他测试文件规模估算）
