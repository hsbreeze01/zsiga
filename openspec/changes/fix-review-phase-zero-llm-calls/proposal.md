# Proposal: Fix Review Phase - 0 LLM Calls Bug

## Summary

Review 阶段存在严重 bug：28 次运行，100% 失败率，0 个 LLM 调用，0 个 tool 调用，0 prompt tokens。Review 子代理根本没有启动。

## Evidence

从 zsiga.db stats_snapshots 提取的数据：
```
review: {
  count: 28,
  pass_rate: 0.0,
  avg_turns: 0.0,
  avg_seconds: 99.1,
  total_llm_calls: 0,
  total_tool_calls: 0,
  total_prompt_tokens: 0,
  total_completion_tokens: 0
}
```

最近 3 次 news-backfill-and-cleanup 的 review 阶段全部失败：
- session 152: implement success, review fail (0 calls, 14.9s)
- session 153: implement success, review fail (0 calls, 440.7s) 
- session 154: implement success, review fail (0 calls, 13.8s)

所有其他阶段正常（enrich 100%, implement 93.9%, deliver 100%）。

## Requirements

1. **自己诊断根因**：阅读 orchestrator.py 中 phase_review() 的实现，找出为什么子代理不启动
2. **常见嫌疑点**：
   - review 阶段的 agent 是否正确初始化？
   - prompt 是否为空或格式错误？
   - 是否有异常被静默吞掉？
   - LLM 调用的 try/except 是否导致静默失败？
   - 子代理的 model 配置是否缺失？
3. **修复后验证**：确保 review 能正常调用 LLM 并输出结果
4. **不要改动其他阶段**：scope 限定在 review 相关代码

## Constraints
- Scope: project=zsiga
- Files: 重点关注 orchestrator.py 中 review 阶段相关代码
- 不要重构其他阶段
- 修复后运行 pytest 确认不破坏现有测试
