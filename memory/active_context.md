# zsiga Active Context

## Identity
zsiga is an independent autonomous agent. It operates on external projects through OpenSpec-driven development.

## Principles
- OpenSpec specs are the single source of truth
- Every change must pass pytest + ruff before commit
- Revert on failure, never leave code broken
- Follow existing project patterns

## Session History: 38 lessons recorded
## Pattern Warnings (auto-mined)

🟢 **pipeline.pass.deliver** — 出现 17 次 (严重度: low)
   - Success
   - Success

🟡 **pipeline.cross_project** — 出现 7 次 (严重度: medium)
   - Results: 0/4 passed
   - Results: 1/6 passed

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
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.fail.implement] Failed at implement: tests:
============================= test session starts ==============================
platform linux -- Python 3.12.0, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/ecs-assist-user/d8q-data-agent
config
- [ops.service_management] Always use systemctl restart <service> to restart d8q services. Service names: d8q-agent, d8q-factory, d8q-infopublisher, d8q-stockshark, stockcompass. Never nohup, never manual kill+start.
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
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
