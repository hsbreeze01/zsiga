# Design: IMPLEMENT 阶段 venv 路径注入

## 架构决策

### 1. 在哪里解析 venv 路径

**决策：在 `orchestrator.py` 的 `_run_phases` 中解析一次，传递给下游所有阶段。**

理由：
- `utils.py` 已有 `_find_venv_python()` 可复用
- 解析一次后可传递给 implementer、fix_loop、eval_fix_loop
- 避免每个阶段重复执行 shell 检测

### 2. 如何将 venv 信息传递给 agent

**决策：通过参数传递给 `implement()` 函数，在 `IMPLEMENTER_SYSTEM` prompt 末尾追加 venv 配置段。**

理由：
- 不修改 `AgentLoop` 或 `register_tools` 接口
- 仅在 system prompt 中追加指令，LLM 会自然遵循
- 与现有的 `project_context` 注入模式一致

### 3. venv 路径解析优先级

1. `TargetConfig.venv_path` — 用户显式配置
2. 自动检测 `{target_path}/.venv/bin/python`
3. 自动检测 `{target_path}/venv/bin/python`
4. 无 venv → 不注入提示

## 数据流

```
zsiga.yaml (venv_path?)
       ↓
TargetConfig.venv_path
       ↓
orchestrator._run_phases()
       ↓ resolve_venv_python(target_path, project_config, transport)
       ↓
venv_python: str | None
       ↓
  ┌─────────────────┐
  │ implement()     │ ← 注入到 IMPLEMENTER_SYSTEM prompt
  │ _fix_loop()     │ ← 追加到修复 prompt
  │ _eval_fix_loop()│ ← 追加到修复 prompt
  └─────────────────┘
```

## 修改文件清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `zsiga/config.py` | MODIFIED | `TargetConfig` 新增 `venv_path` 字段；`load_config` 解析该字段 |
| `zsiga/pipeline/utils.py` | MODIFIED | 将 `_find_venv_python` 重命名为 `find_venv_python` 并公开导出；新增 `resolve_venv_python` 函数（优先级合并） |
| `zsiga/pipeline/implementer.py` | MODIFIED | `implement()` 接受 `venv_python` 参数；`IMPLEMENTER_SYSTEM` 动态追加 venv 配置段 |
| `zsiga/pipeline/orchestrator.py` | MODIFIED | `_run_phases` 中调用 `resolve_venv_python` 获取路径，传递给 `implement()`、`_fix_loop()`、`_eval_fix_loop()`；三个 fix prompt 中追加 venv 提示 |

## Prompt 注入内容示例

当 `venv_python = "/home/user/project/.venv/bin/python"` 时，追加到 system prompt：

```
## venv 配置（必须遵守）

项目使用 venv，所有命令 MUST 使用以下路径：
- Python: /home/user/project/.venv/bin/python
- pip: /home/user/project/.venv/bin/python -m pip
- pytest: /home/user/project/.venv/bin/python -m pytest

规则：
- 绝对不要使用 python、python3、pip、pip3 — 必须使用上方完整路径
- 不要 pip install 项目已有依赖（venv 已包含所有依赖）
- 只有在 import 失败且确认 venv 中确实缺少该包时才安装
```
