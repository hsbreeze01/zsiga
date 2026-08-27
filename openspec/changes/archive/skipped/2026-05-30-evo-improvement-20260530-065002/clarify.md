# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 `create_transport`，3 个类 `Transport` / `LocalTransport` / `SSHTransport`）编写完整单元测试，目标文件 `tests/test_transport.py`。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + LocalTransport 测试**（预估复杂度：低，预估 token：~2500 / 无历史参考）
  - 范围：`Transport` 抽象基类（`run_shell` / `close`）、`LocalTransport.run_shell`（subprocess 调用）
  - 文件：`tests/test_transport.py`（新建）
  - 要点：mock `subprocess.run`；验证返回值、stderr 处理、异常路径

- [ ] 2. **SSHTransport 测试**（预估复杂度：中，预估 token：~3500 / 无历史参考）
  - 范围：`SSHTransport.__init__`、`_ensure_control`、`_base_args`、`_target`、`run_shell`、`close`
  - 文件：`tests/test_transport.py`（追加）
  - 要点：mock `subprocess.run`（ssh 控制建连 + 远程命令）；验证控制路径创建、命令拼接、`close` 清理；需构造含 `ssh` 配置的 `target_config` fixture

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低，预估 token：~2000 / 无历史参考）
  - 范围：`create_transport(target_config)` — 根据 `transport` 字段返回 `LocalTransport` 或 `SSHTransport`
  - 文件：`tests/test_transport.py`（追加）
  - 要点：两路分支覆盖（`transport=local` → `LocalTransport`；`transport=ssh` → `SSHTransport`）；可选：无效 transport 值异常路径

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 全部公开方法
- 使用 mock 隔离 subprocess / SSH 外部依赖
- 测试通过 `ruff check` + `pytest` 零失败

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不测试私有方法内部实现细节（仅通过公开接口验证行为）
- 不引入新依赖

### 依赖的外部条件
- `zsiga/transport.py` 源码结构不变（当前 96 行，3 类 1 函数）
- pytest + ruff 已在项目中可用
- `target_config` 数据结构需与 `zsiga/config.py` 中 `TargetConfig` 兼容

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥ 8 个 `def test_` 函数（覆盖 3 个类 + 1 个工厂函数的主要路径）
2. `python -m pytest tests/test_transport.py` 退出码 0，全部测试通过
3. `ruff check tests/test_transport.py` 零错误
4. `test_create_transport` 函数名存在（满足 BAC-02）

### 验收方式
- `test -f tests/test_transport.py`（BAC-01）
- `grep -c 'def test_' tests/test_transport.py` ≥ 8
- `python -m pytest tests/test_transport.py -q` 退出码 0（BAC-04）
- `ruff check tests/test_transport.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）

### 项目部署分支
- 待确认（proposal 标注 `project=zsiga`，即自身项目）

### 已知风险
- **SSHTransport 内部实现细节**：`_ensure_control` 可能涉及 subprocess 调用 ssh 控制建连，mock 需精确匹配命令模式；若源码使用 `paramiko` 而非 subprocess，mock 策略需调整
- **历史同类 proposal 多次 skipped**：archive 中有 2 个同类 transport 测试 proposal 被跳过（20260530-043915、20260530-054103），需确保本次测试文件命名与内容不与存档冲突

### 预估 token 消耗
- prompt: ~8000（3 轮 × ~2500 + 上下文）
- completion: ~4000（3 个任务，每轮 ~1300 输出）
- 数据来源: 无历史参考（同类任务均未完成交付）
