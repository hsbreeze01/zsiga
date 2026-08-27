# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，3 个类 + 1 个工厂函数）添加单元测试文件 `tests/test_transport.py`，覆盖 `Transport` 基类、`LocalTransport`、`SSHTransport`、`create_transport()` 的公开行为。使用 mock 隔离 subprocess 调用，确保测试可独立运行。

### 拆解后的子任务
- [ ] 1. **Transport 基类 + LocalTransport 测试**（预估复杂度：低, 预估 token：~2000）
  - 验证 `Transport` 是抽象基类：`run_shell` raise `NotImplementedError`，`close` 为空操作
  - 验证 `LocalTransport.run_shell` 正确转发 subprocess.run 参数，返回 `{exit_code, stdout, stderr}` dict
  - 覆盖 `subprocess.TimeoutExpired` 和 `OSError` 异常路径
  - 文件范围：`tests/test_transport.py`（新建）

- [ ] 2. **SSHTransport 全生命周期测试**（预估复杂度：中, 预估 token：~3500）
  - 验证 `__init__` 正确存储 ssh 配置（host/user/key_path）
  - 验证 `_target` 属性拼接 `user@host`
  - 验证 `_base_args` 返回正确的 ssh control master 参数列表
  - 验证 `_ensure_control` 在 control socket 不存在时建立连接
  - 验证 `run_shell` 通过 ssh 执行命令并返回标准 dict
  - 验证 `close` 关闭 control master
  - 覆盖超时和异常兜底路径（exit_code=-1）
  - Mock 策略：`@patch("zsiga.transport.subprocess.run")` + 直接设置 `_control_path` 跳过 `_ensure_control`
  - 文件范围：`tests/test_transport.py`

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~1000）
  - 验证含 `ssh` 属性的 target_config 返回 `SSHTransport` 实例
  - 验证无 `ssh` 属性的 target_config 返回 `LocalTransport` 实例
  - 使用 `types.SimpleNamespace` 构造轻量 config 对象
  - 文件范围：`tests/test_transport.py`

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 transport.py 全部公开符号（4 个）
- 使用 `pytest` + `unittest.mock` 隔离 subprocess
- 参考 archive 中已有蓝本（如 `2026-05-30-evo-improvement-20260530-043915/tests/`）

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `conftest.py` 或其他测试文件
- 不修改 `pyproject.toml`、`requirements.txt` 等配置文件
- 不添加集成测试或端到端测试

### 依赖的外部条件
- Python ≥3.10 运行时可用
- `pytest` 和 `unittest.mock` 可用（项目已有依赖）
- `zsiga/transport.py` 当前 API 稳定（96 行，无近期变更风险）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 `test_create_transport` 函数
2. 文件中至少包含 8 个 `def test_` 函数，覆盖 4 个公开符号（Transport、LocalTransport、SSHTransport、create_transport）
3. `python -m pytest tests/test_transport.py` 退出码 0，无 ruff lint 错误
4. 所有 subprocess 调用通过 mock 隔离，测试可在无网络/无 SSH 环境下运行

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` 确认测试函数数量 ≥ 8
- `grep -q 'test_create_transport' tests/test_transport.py` 确认工厂函数测试存在
- `python -m pytest tests/test_transport.py -v` 退出码 0
- `ruff check tests/test_transport.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/conftest.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
deploy

### 已知风险
- **20+ 次空转历史**：此任务在 archive/skipped 中出现 20+ 次，全部未落地。核心难点是 SSHTransport 的 `_ensure_control` 和 `run_shell` 都调用 `subprocess.run`，mock 的 `side_effect` 顺序必须精确匹配调用顺序，否则测试会误失败。建议直接设置 `_control_path` 属性跳过 `_ensure_control`，避免顺序依赖
- **basename 匹配陷阱**：自演进引擎可能因 basename 不匹配而反复生成同类 proposal，但本任务聚焦执行，不涉及引擎修复

### 预估 token 消耗
- prompt: ~4000（读取 transport.py 96 行 + 编写测试上下文）
- completion: ~2500（生成 ~250 行测试代码）
- 数据来源: 无历史参考（该任务从未成功落地），按模块规模估算
