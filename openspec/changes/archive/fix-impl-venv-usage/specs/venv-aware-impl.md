# Delta Spec: IMPLEMENT 阶段使用项目 venv Python

## ADDED Requirements

### Requirement: venv 路径自动检测

系统 SHALL 在每个 target 的 IMPLEMENT 阶段开始前，自动检测目标项目的 Python venv 路径。

检测优先级（按顺序尝试）：
1. `TargetConfig.venv_path` 显式配置
2. `{target_path}/.venv/bin/python` 文件存在
3. `{target_path}/venv/bin/python` 文件存在

若均不存在，系统 SHALL 回退到系统默认 Python，不报错。

#### Scenario: 目标项目有 .venv 目录

```gherkin
Given 目标项目路径为 /home/user/myproject
And /home/user/myproject/.venv/bin/python 文件存在
When 系统准备 IMPLEMENT 阶段
Then 检测到的 venv python 路径为 "/home/user/myproject/.venv/bin/python"
```

#### Scenario: TargetConfig 中显式配置了 venv_path

```gherkin
Given zsiga.yaml 中 target 配置了 venv_path: "/opt/custom/env/bin/python"
When 系统准备 IMPLEMENT 阶段
Then 使用配置的路径 "/opt/custom/env/bin/python" 作为 venv python
And 不进行自动检测
```

#### Scenario: 项目没有 venv

```gherkin
Given 目标项目路径为 /home/user/myproject
And 该目录下不存在 .venv/bin/python 和 venv/bin/python
And TargetConfig 未配置 venv_path
When 系统准备 IMPLEMENT 阶段
Then 检测结果为空
And agent prompt 中不注入 venv 路径提示
```

---

### Requirement: IMPLEMENT 阶段 prompt 注入 venv 路径

当检测到 venv python 路径时，系统 SHALL 在 implementer 的 system prompt 中注入明确的 Python 路径指令，告知 agent 使用 venv python 执行所有 Python 相关操作。

注入内容 MUST 包含：
- `venv_python` 的绝对路径
- 明确指令：使用 `{venv_python}` 替代 `python`、`python3`
- 明确指令：使用 `{venv_python} -m pip` 替代 `pip`、`pip3`
- 明确指令：使用 `{venv_python} -m pytest` 替代 `pytest`（除非 pytest 命令已直接可用）
- 明确指令：不要安装项目 requirements.txt 中已有的依赖

#### Scenario: 有 venv 时的 prompt 注入

```gherkin
Given 检测到 venv python 路径为 "/home/user/myproject/.venv/bin/python"
When 系统构建 IMPLEMENT 阶段的 system prompt
Then prompt 中包含一段 "venv 配置" 区域，内容包含:
  | 变量            | 值                                    |
  | venv_python     | /home/user/myproject/.venv/bin/python |
  | pip 命令        | /home/user/myproject/.venv/bin/python -m pip |
  | pytest 命令     | /home/user/myproject/.venv/bin/python -m pytest |
And 指令说明 "所有 Python/pip/pytest 命令必须使用上方路径"
And 指令说明 "不要 pip install 项目已有依赖"
```

#### Scenario: 无 venv 时不注入

```gherkin
Given 未检测到 venv python 路径
When 系统构建 IMPLEMENT 阶段的 system prompt
Then prompt 中不包含任何 venv 相关指令
```

---

### Requirement: FIX 循环 prompt 同样注入 venv 路径

`_fix_loop` 和 `_eval_fix_loop` 中的修复 prompt SHALL 同样注入 venv 路径信息，确保修复阶段也使用正确的 Python。

#### Scenario: fix loop 使用 venv

```gherkin
Given 检测到 venv python 路径为 "/home/user/project/.venv/bin/python"
And IMPLEMENT 阶段机械验证失败，进入 _fix_loop
When 系统构建修复 prompt
Then 修复 prompt 中包含同样的 venv 路径指令
```

---

### Requirement: TargetConfig 支持 venv_path 配置

`zsiga.yaml` 的 target 配置 SHALL 支持可选的 `venv_path` 字段，允许用户显式指定 venv python 的路径。

#### Scenario: yaml 配置 venv_path

```gherkin
Given zsiga.yaml 中包含:
  """
  targets:
    myapp:
      path: /home/user/myapp
      venv_path: /home/user/myapp/.venv/bin/python
  """
When 加载配置
Then TargetConfig.venv_path 为 "/home/user/myapp/.venv/bin/python"
```

#### Scenario: yaml 未配置 venv_path

```gherkin
Given zsiga.yaml 的 target 配置中未包含 venv_path 字段
When 加载配置
Then TargetConfig.venv_path 为 None
And 系统将通过自动检测确定 venv 路径
```
