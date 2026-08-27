# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 类 + 1 工厂函数）创建单元测试文件 `tests/test_transport.py`，覆盖所有公开接口。模块包含 `Transport` 基类、`LocalTransport`、`SSHTransport` 三个类及 `create_transport()` 工厂函数。不修改源码。

### 拆解后的子任务
- [ ] 1. Transport 基类 + LocalTransport 测试（预估复杂度：低, 预估 token：~3000）
  - 文件范围：`tests/test_transport.py`（新建）
  - 覆盖点：`Transport` 基类抽象接口（`run_shell`/`close` 默认行为或 NotImplementedError）；`LocalTransport.run_shell` 正常调用 subprocess.run 并返回 `{"exit_code", "stdout", "stderr"}` 字典；subprocess 超时（`TimeoutExpired`）和 `OSError` 异常路径
  - Mock 策略：`@patch("zsiga.transport.subprocess.run")` 隔离外部调用
  - 验证：`pytest tests/test_transport.py -k "Local"` 退出码 0

- [ ] 2. SSHTransport 全方法测试（预估复杂度：中, 预估 token：~5000）
  - 文件范围：`tests/test_transport.py`（同一文件追加）
  - 覆盖点：`__init__` 参数存储与默认值；`_ensure_control` 创建控制路径（mock `subprocess.run` + `os.makedirs`）；`_base_args` 返回正确 SSH 参数列表；`_target` 格式化 user@host；`run_shell` 组装完整命令并执行（正常 + TimeoutExpired + OSError）；`close` 关闭控制连接
  - Mock 策略：`@patch("zsiga.transport.subprocess.run")`；手动设置 `t._control_path` 跳过 `_ensure_control`（遵循已有蓝本模式）；使用 `SimpleNamespace` 模拟 `TargetConfig`
  - 验证：`pytest tests/test_transport.py -k "SSH"` 退出码 0

- [ ] 3. create_transport 工厂函数测试（预估复杂度：低, 预估 token：~2000）
  - 文件范围：`tests/test_transport.py`（同一文件追加）
  - 覆盖点：`transport="local"` 返回 `LocalTransport` 实例；`transport="ssh"` 返回 `SSHTransport` 实例；未知的 transport 类型抛出预期异常（ValueError 或 KeyError）
  - 验证：`pytest tests/test_transport.py -k "create_transport"` 退出码 0

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含 ≥10 个 `def test_` 函数
- 覆盖 `Transport`、`LocalTransport`、`SSHTransport` 的全部公开方法
- 覆盖 `create_transport()` 工厂函数的全部分支
- 使用 mock 隔离 subprocess / 文件系统，确保测试可独立运行
- 满足 BAC-01 ~ BAC-04 全部验收标准

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/config.py` 或其他任何源码文件
- 不修改 `pyproject.toml`、`requirements.txt` 等配置文件
- 不添加集成测试或端到端测试
- 不处理私有方法 `_ensure_control`、`_base_args`、`_target` 的直接测试（通过公开方法间接覆盖即可，除非需要独立验证才单独测试）

### 依赖的外部条件
- `zsiga/transport.py` 保持当前结构不变（3 类 + 1 工厂函数）
- `subprocess` 模块可通过 `unittest.mock.patch` 正常 mock
- 项目 `pytest` 环境可用（`requirements.txt` 中未显式声明但项目测试目录已大量使用）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且为新建（非修改已有文件）
2. 文件中包含函数 `test_create_transport`（BAC-02）
3. 文件中包含至少 10 个 `def test_` 函数，覆盖全部 3 个类和工厂函数（超出 BAC-03 最低要求）
4. `python -m pytest tests/test_transport.py` 退出码 0，无 FAIL / ERROR（BAC-04）
5. `python -m ruff check tests/test_transport.py` 无 lint 错误

### 验收方式
- 文件存在性：`test -f tests/test_transport.py && echo OK`
- 函数存在性：`grep -c "def test_" tests/test_transport.py` ≥ 10；`grep "def test_create_transport" tests/test_transport.py` 匹配
- 测试通过：`python -m pytest tests/test_transport.py -v` 退出码 0
- Lint 通过：`python -m ruff check tests/test_transport.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `zsiga/config.py`
- `pyproject.toml`
- `requirements.txt`
- 任何 `tests/` 下已有的测试文件

### 项目部署分支
deploy

### 已知风险
- **历史空转风险**：同名 proposal `add-tests-transport` 已在 archive 中 skipped 20+ 次，蓝本代码从未落地到 `tests/test_transport.py`。根因可能是 deploy 分支 drift 或 deliver 阶段失败。执行时需确保最终文件确实写入 `tests/test_transport.py`。
- **SSHTransport._ensure_control 依赖真实 subprocess**：该方法调用 `ssh -o ControlMaster=auto -N` 建立控制连接，测试中必须 mock 掉或通过手动设置 `_control_path` 跳过。
- **TargetConfig 导入耦合**：`create_transport` 和 `SSHTransport.__init__` 接受 `target_config` 参数，需从 `zsiga.config` 获取类型。为避免深层导入，推荐使用 `SimpleNamespace` 或 `MagicMock` 模拟。

### 预估 token 消耗
- prompt: ~8000（含 transport.py 源码 + 已有蓝本参考 + mock 策略）
- completion: ~5000（约 250-300 行测试代码生成）
- 数据来源: 无历史参考（同名 proposal 均 skipped 未执行）
