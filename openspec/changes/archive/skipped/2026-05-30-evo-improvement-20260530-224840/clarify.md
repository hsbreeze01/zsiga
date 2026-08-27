# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 + 3 个类）创建 `tests/test_transport.py` 单元测试文件，覆盖公开接口，使用 mock 隔离 subprocess 等外部依赖。

### 拆解后的子任务
- [ ] 1. **Transport 抽象基类 + LocalTransport 测试**：验证 `Transport` 不可直接实例化（抽象方法），验证 `LocalTransport.run_shell` 调用 `subprocess.run` 并返回结果 (预估复杂度：低, 预估 token：~1500)
- [ ] 2. **SSHTransport 测试**：覆盖 `__init__` 参数存储、`_ensure_control` 幂等性（重复调用不重复创建）、`_base_args` 返回正确 ssh 参数、`_target` 格式化、`run_shell` 通过 ssh 执行命令、`close` 清理控制路径 (预估复杂度：中, 预估 token：~2500)
- [ ] 3. **create_transport 工厂函数测试**：验证根据 `target_config` 的 `transport` 字段分派到 `LocalTransport` 或 `SSHTransport`，覆盖两种分支 (预估复杂度：低, 预估 token：~1000)
- [ ] 4. **pytest 验证通过**：确保 `python -m pytest tests/test_transport.py` 退出码 0，无 import 错误或 fixture 问题 (预估复杂度：低, 预估 token：~500)

## 边界

### IN scope
- 新建 `tests/test_transport.py` 文件
- 覆盖 `Transport`、`LocalTransport`、`SSHTransport` 三个类的公开方法
- 覆盖 `create_transport()` 工厂函数的分派逻辑
- 使用 `unittest.mock` 隔离 `subprocess.run` 调用
- BAC-01~04 全部满足

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `tests/conftest*.py` 或其他现有测试文件
- 不添加集成测试（真实 SSH 连接等）
- 不涉及 transport 模块的性能或安全测试

### 依赖的外部条件
- `zsiga/transport.py` 模块可正常 import（无语法错误）
- `unittest.mock` 可用（Python 标准库）
- 项目测试环境已配置 pytest

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 测试中包含 `test_create_transport` 函数（BAC-02）
3. `python -m pytest tests/test_transport.py` 退出码为 0（BAC-04）
4. 所有 mock 隔离外部依赖，不产生真实 subprocess/SSH 调用

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` 计数 ≥3
- `python -m pytest tests/test_transport.py -v` 全部 PASSED
- `ruff check tests/test_transport.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `tests/conftest*.py`
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- 待确认（从 `zsiga.yaml` 中 zsiga-self target 的 deploy_branch 字段读取）

### 已知风险
- **循环空转历史**：archive/skipped 中存在 20+ 次同主题 proposal 未落地记录，需确保本次一次性交付完成
- **SSHTransport mock 复杂度**：`SSHTransport` 内部管理 `control_path` 状态和多次 subprocess 调用（`_ensure_control` → `ssh -O check`、`ssh -N -f -o ControlMaster`、`run_shell` → `ssh`），mock 需精确匹配调用序列
- **deploy branch drift**：部署分支在处理期间可能被外部修改

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（同类 proposal 均未执行到完成）
