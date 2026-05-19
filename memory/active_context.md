# zsiga Active Context

## Identity
zsiga is an independent autonomous agent. It operates on external projects through OpenSpec-driven development.

## Principles
- OpenSpec specs are the single source of truth
- Every change must pass pytest + ruff before commit
- Revert on failure, never leave code broken
- Follow existing project patterns

## Session History: 48 lessons recorded
## Pattern Warnings (auto-mined)

🟢 **pipeline.pass.deliver** — 出现 17 次 (严重度: low)
   - Success
   - Success

🟡 **pipeline.cross_project** — 出现 16 次 (严重度: medium)
   - Results: 1/4 passed
   - Results: 0/4 passed

🔴 **pipeline.fail.implement** — 出现 6 次 (严重度: high)
   - Failed at implement: lint:
E701 Multiple statements on one line (colon)
   --> src/intelligent_data_agent/tasks/multi_source_crawl.py:196:35
    |
194 |             matched = _match_keywords(it.title, keywords)
195 |     
   - Failed at implement: lint:
E701 Multiple statements on one line (colon)
   --> src/intelligent_data_agent/tasks/multi_source_crawl.py:201:35
    |
199 |             matched = _match_keywords(it.title, keywords)
200 |     


## Recent Lessons
- [pipeline.fail.verify.unknown] Failed at verify: review error and adjust approach
- [pipeline.fail.implement.test_failure] Check test output for specific assertion errors; verify test expectations match implementation API
- [pipeline.fail.implement.unknown] Failed at implement: review error and adjust approach
- [pipeline.cross_project] Results: 1/6 passed
- [pipeline.cross_project] Results: 1/2 passed
- [pipeline.cross_project] Results: 1/6 passed
- [pipeline.cross_project] Results: 1/2 passed
- [pipeline.cross_project] Results: 0/4 passed
- [pipeline.cross_project] Results: 1/6 passed
- [pipeline.cross_project] Results: 1/6 passed
- [pipeline.cross_project] Results: 1/2 passed
- [pipeline.cross_project] Results: 0/4 passed
- [pipeline.cross_project] Results: 1/6 passed
- [pipeline.cross_project] Results: 1/3 passed
- [pipeline.cross_project] Results: 1/4 passed
- [pipeline.cross_project] Results: 0/4 passed
- [pipeline.cross_project] Results: 1/4 passed
- [pipeline.cross_project] Results: 0/4 passed
- [pipeline.cross_project] Results: 0/2 passed
- [pipeline.fail.verify.unknown] Failed at verify: review error and adjust approach
