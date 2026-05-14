# Proposal: 修复 IMPLEMENT 阶段使用系统 Python 而非 venv 的问题

## 背景
zsiga 在 IMPLEMENT 阶段运行测试和安装依赖时，使用系统 `python3` 而非项目的 `venv/bin/python`。这导致：
1. 每次运行都花大量 turns 安装已有依赖（flask, pandas, pytest 等）
2. 测试因 import 失败而报错，消耗修复 turns
3. 30 turns 上限经常不够用

## 目标
修改 IMPLEMENT 阶段的工具调用，让 agent 使用项目 venv 中的 Python：
- `python` / `python3` → `venv/bin/python`（或 target 配置中的 venv 路径）
- `pip install` → `venv/bin/pip install`（但大部分情况不需要安装，venv 已有）

## 变更范围
- `zsiga/pipeline/orchestrator.py` 或 `zsiga/agent/tools.py` — 在 IMPLEMENT prompt 中注入 venv 路径
- `zsiga.yaml` — 可选：添加 `venv_path` 配置项

## 成功标准
- IMPLEMENT 阶段使用 venv python 而非系统 python
- 不再花 turns 安装已有依赖
- compass 项目测试可直接运行
