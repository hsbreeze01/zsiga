# Tasks: IMPLEMENT 阶段 venv 路径注入

## 1. 配置层

- [x] **1.1** 在 `TargetConfig` 中添加 `venv_path` 字段，并在 `load_config` 中解析 `targets.<name>.venv_path`

## 2. venv 检测函数

- [x] **2.1** 在 `zsiga/pipeline/utils.py` 中新增公开函数 `resolve_venv_python(target_path, project_config, transport)`，合并配置优先级（`venv_path` → `.venv` → `venv` → None），并将原 `_find_venv_python` 内部逻辑整合进来

## 3. Prompt 注入

- [x] **3.1** 修改 `zsiga/pipeline/implementer.py`：`implement()` 接受可选参数 `venv_python`，当非空时在 `IMPLEMENTER_SYSTEM` 末尾追加 venv 配置提示段（含 Python/pip/pytest 完整路径及使用规则）

- [x] **3.2** 修改 `zsiga/pipeline/orchestrator.py`：在 `_run_phases` 中调用 `resolve_venv_python` 获取 venv 路径，传递给 `implement()`；同时修改 `_fix_loop` 和 `_eval_fix_loop` 签名接受 `venv_python`，在修复 prompt 中追加同样的 venv 路径提示

## 4. 验证

- [x] **4.1** 确认项目自身通过 `ruff check` 和 `pytest`（无新增 lint 错误、无回归）
