# Tasks: l5-intent-gate — Phase 0 Intent Gate

## 1. Intent Router Core (intent_router.py)

- [x] 1.1 重写 IntentType 枚举为 6 种意图（RESEARCH/IMPLEMENTATION/INVESTIGATION/EVALUATION/FIX/OPEN_ENDED），更新 Intent dataclass 添加 verbalization 字段，实现 `_verbalize()` 函数和扩展关键词模式，更新 `classify()` 和 `route()` 函数

## 2. Orchestrator Routing (orchestrator.py)

- [x] 2.1 更新 `_process_change()` 方法：处理新的 6 种路由目标（dispatch explore/diagnoser/review 子代理、pipeline_fix 缩短管线、ask_user 澄清），更新 IntentType 导入和过滤逻辑

## 3. Tests

- [x] 3.1 添加 tests/test_intent_router.py：覆盖所有 6 种意图分类、verbalization 输出、边界情况（空消息、混合关键词）、路由映射正确性
