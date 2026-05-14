# Proposal: Fix Self Lint Issues (L3 Validation)

## Summary
zsiga 使用 diagnostics 工具扫描自身源码的 lint 问题（unused imports, unused variables, f-string without placeholders），用 goto_definition 和 find_references 确认后逐一修复。

## Motivation
L3 验收要求 zsiga 用 LSP 工具定位自身代码问题并修复。当前 `ruff check zsiga/` 报告 54 个问题，清理这些问题既改善代码质量，又验证 LSP 工具链的端到端能力。

## Expected Behavior
- 使用 `diagnostics` 工具扫描 `zsiga/agent/loop.py`、`zsiga/agent/tools.py`、`zsiga/__main__.py` 等文件
- 使用 `goto_definition` 确认 import 是否真的未使用（排除动态引用）
- 使用 `find_references` 验证变量/函数是否无引用
- 修复以下类型的问题：
  - F401: unused imports（`json` in tools.py, `os` in tools.py, `asyncio`/`subprocess`/`Path` in loop.py, `threading` in __main__.py）
  - F541: f-string without placeholders（__main__.py 中的多个 print 语句）
  - F841: unused variables（`llm_ms`/`result_lines` in loop.py, `content` in compaction.py）
  - F401: unused imports in metrics/（collector.py, dashboard.py）
- 修复后 `ruff check zsiga/` 应报告 0 errors
- 所有现有测试仍然通过

## Scope
- 仅修改 `zsiga/` 目录下的 Python 文件
- 不修改 tests/ 目录
- 不修改配置文件（zsiga.yaml）
- 不添加新功能，只做 lint 清理
