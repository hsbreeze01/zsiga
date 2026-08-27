# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 `create_transport`，3 个类 `Transport`/`LocalTransport`/`SSHTransport`）编写单元测试文件 `tests/test_transport.py`，覆盖公开 API 的核心行为路径，使用 mock 隔离 subprocess 和 SSH 外部依赖。

### 拆解后的子任务
- [ ] 1. Transport 基类与 LocalTransport 测试 (预估复杂度：低, 预估 token：~3000)
  - 验证 `Transport` 基类 `run_shell()` 抛出 `NotImplementedError`，`close()` 无操作
  - 验证 `LocalTransport.run_shell()` 正确调用 `subprocess.run` 并返回 `{"exit_code", "stdout", "stderr"}` 字典
  - 验证 `LocalTransport.close()` 无操作
- [ ] 2. SSHTransport 测试 (预估复杂度：中, 预估 token：~4000)
  - 验证 `__init__` 正确解析 host/user/port/key_path 参数，`key_path` 做 `expanduser`
  - 验证 `_ensure_control` 构建并复用 SSH ControlMaster 连接
  - 验证 `run_shell()` 通过 SSH 执行命令并返回标准退出码字典
  - 验证超时场景返回 `exit_code=-1`
  - 验证 `close()` 关闭 ControlMaster socket
- [ ] 3. create_transport 工厂函数测试 (预估复杂度：低, 预估 token：~2000)
  - 验证 `target_config` 无 `.ssh` 属性时返回 `LocalTransport` 实例
  - 验证 `target_config` 有 `.ssh` 属性时返回 `SSHTransport` 实例
  - 验证返回对象类型是 `Transport` 子类

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含上述 3 组测试
- 使用 `unittest.mock` 隔离 `subprocess.run` 和 SSH 命令执行
- 覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的公开接口

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不测试私有方法内部实现细节（仅通过公开接口间接覆盖）
- 不测试跨模块集成（如与 config.py 的 target_config 构造）

### 依赖的外部条件
- `zsiga/transport.py` 模块可正常 import
- `unittest.mock` 可用（Python 标准库）
- pytest 框架已安装

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥6 个 `def test_` 函数
2. `test_create_transport` 函数存在于测试文件中
3. `python -m pytest tests/test_transport.py` 退出码为 0
4. 测试覆盖 `Transport` 基类、`LocalTransport`、`SSHTransport`、`create_transport` 四个公开符号

### 验收方式
- 检查 `tests/test_transport.py` 文件存在
- `grep -c 'def test_' tests/test_transport.py` ≥ 6
- `grep 'test_create_transport' tests/test_transport.py` 匹配成功
- `python -m pytest tests/test_transport.py -v` 全部通过（退出码 0）
- `ruff check tests/test_transport.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析，不修改源码）

### 项目部署分支
- deploy

### 已知风险
- 该 proposal 已在 archive 中出现 20+ 次均被 skipped，属 auto-generated loop 模式。本轮需确保完整交付，避免再次空转
- `SSHTransport` 的 `_ensure_control` 涉及实际 SSH socket 文件操作，必须完全 mock 以避免环境依赖
- `create_transport` 依赖 `target_config` 对象（需 `.ssh` 属性），测试中需构造合适的 mock/stub 对象

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考（同类 proposal 从未成功落地）
