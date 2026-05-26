# 诊断报告: fix-review-verdict-parser
总尝试次数: 1
需要人工介入: 否

## 失败记录
- 第1次 (verify): lint:
F821 Undefined name `SubAgentResult`
  --> zsiga/agent/reviewer.py:62:6
   |
60 |     max_turns: int = 10,
61 |     timeout_seconds: int = 180,
62 | ) -> SubAgentResult:
   |      ^^^^^^^^^^^^^^
63 |     """Dispatch review-role sub-agent to analyze implementation against specs.
   |
Found 1 error. [策略: same]

## 根因假设
所有失败发生在同一阶段 (verify)，可能是该阶段的系统性问题

## 建议操作
尝试不同策略