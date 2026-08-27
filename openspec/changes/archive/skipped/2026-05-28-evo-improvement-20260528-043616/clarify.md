# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行）新建 `tests/test_transport.py`，覆盖公开 API：抽象基类 `Transport`、`LocalTransport`、`SSHTransport`、工厂函数 `create_transport()`。使用 mock 隔离 `subprocess` 调用，不修改源码。

### 拆解后的子任务

- [ ] 1. **Transport 基类 & LocalTransport 测试**（预估复杂度：低, 预估 token：~2000 / 无历史参考）
  - 验证 `Transport` 是抽象基类，直接实例化应抛 `TypeError`
  - `LocalTransport.run_shell()` 正常路径：mock `subprocess.run`，验证返回 `CompletedProcess` 并转发参数（`shell=True`）
  - `LocalTransport.close()` 为空操作，调用不报错
  - 文件范围：`tests/test_transport.py`（新建）

- [ ] 2. **SSHTransport 测试**（预估复杂度：中, 预估 token：~3500 / 无历史参考）
  - `__init__`：传入含 ssh 字段的 config，验证 host/port/user/key_path 属性正确存储
  - `_ensure_control`：mock `subprocess.run`，验证建立 SSH control master 的命令参数
  - `_base_args`：验证返回的参数列表包含 `ssh`、control socket、用户@主机
  - `_target`：验证格式为 `user@host`
  - `run_shell()`：mock `subprocess.run`，验证通过 SSH 执行命令（拼接 `_base_args` + cmd）
  - `close()`：mock `subprocess.run`，验证发送 SSH control exit 命令
  - 文件范围：`tests/test_transport.py`（同一文件）

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低, 预估 token：~1500 / 无历史参考）
  - config 无 ssh 字段 → 返回 `LocalTransport` 实例
  - config 有 ssh 字段 → 返回 `SSHTransport` 实例
  - 验证返回类型为 `Transport` 子类
  - 文件范围：`tests/test_transport.py`（同一文件）

## 边界

### IN scope
- 新建 `tests/test_transport.py`
- 测试 `Transport`（抽象基类）、`LocalTransport`、`SSHTransport` 的公开方法
- 测试 `create_transport()` 工厂函数
- 使用 `unittest.mock.patch` 隔离所有 `subprocess.run` 调用
- 通过 ruff lint 检查

### OUT of scope
- 修改 `zsiga/transport.py` 源码
- 修改其他测试文件
- 修改 `conftest.py` 或测试基础设施
- 端到端 SSH 连接测试

### 依赖的外部条件
- `unittest.mock`（stdlib，无需额外安装）
- `subprocess` 模块可通过 mock 完全隔离
- `zsiga/transport.py` 存在且接口稳定（96 行，0 lint 问题）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在
2. 文件中包含 `test_create_transport` 函数
3. 文件中包含至少 5 个 `def test_` 函数（覆盖基类、LocalTransport、SSHTransport、工厂函数）
4. `python -m pytest tests/test_transport.py` 退出码 0
5. `ruff check tests/test_transport.py` 无错误

### 验收方式
- 文件存在性检查：`ls tests/test_transport.py`
- 函数存在性检查：`grep -c 'def test_' tests/test_transport.py`
- pytest 执行：`python -m pytest tests/test_transport.py -v`
- lint 检查：`ruff check tests/test_transport.py`

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/conftest_zsiga.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- main

### 已知风险
- SSHTransport 内部方法（`_ensure_control`、`_base_args`、`_target`）为私有方法，测试需通过白盒方式直接调用或通过公开方法间接覆盖；mock 链条较长（`__init__` → `_ensure_control` → `subprocess.run`）
- 工厂函数 `create_transport` 依赖 config dict 结构，需构造符合实际 `zsiga.yaml` 中 target 格式的 fixture 数据

### 预估 token 消耗
- prompt: ~3000
- completion: ~4000
- 数据来源: 无历史参考（transport 模块首次测试）
