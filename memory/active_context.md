# zsiga Active Context

## Identity
zsiga is an independent autonomous agent. It operates on external projects through OpenSpec-driven development.

## Principles
- OpenSpec specs are the single source of truth
- Every change must pass pytest + ruff before commit
- Revert on failure, never leave code broken
- Follow existing project patterns
- **NEVER use nohup to start/restart services.** All d8q projects are managed by systemd:
  - d8q-agent.service (dataagent, :8000)
  - d8q-factory.service (:8088)
  - d8q-infopublisher.service (:8089)
  - d8q-stockshark.service (:5000)
  - stockcompass.service (compass)
  - d8q-ghost-browser.service, d8q-xvfb.service, d8q-web.service (infrastructure)
  - Use `systemctl restart <service>` to restart, `systemctl status <service>` to check.
  - Do NOT `kill` processes manually; do NOT `nohup gunicorn` — let systemd manage processes.

## Session History: 20 lessons recorded

## Recent Lessons
- [tools.venv_detection] always detect venv/ first, use venv/bin/python -m pytest/ruff instead of bare commands
- [prompt.verify_efficiency] keep verifier prompt strict: list steps explicitly, cap at 10 turns, forbid re-reading known files
- [verify.changed_files_only] use git diff --name-only since pre_sha to get changed .py files, only lint those
- [pipeline.fail.implement] Failed at implement: lint:
E401 [*] Multiple imports on one line
 --> Ashare/Ashare.py:2:1
  |
1 | # -*- coding:utf-8 -*-    --------------Ashare 股票行情数据双核心版( https://github.com/mpquant/Ashare )
2 | import json, requests, 
- [pipeline.fail.implement] Failed at implement: lint:
E401 [*] Multiple imports on one line
 --> Ashare/Ashare.py:2:1
  |
1 | #-*- coding:utf-8 -*-    --------------Ashare 股票行情数据双核心版( https://github.com/mpquant/Ashare ) 
2 | import json,requests,da
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.fail.implement] Failed at implement: lint:
E702 Multiple statements on one line (semicolon)
  --> src/intelligent_data_agent/server.py:8:31
   |
 6 | from typing import Dict
 7 |
 8 | from dotenv import load_dotenv; load_dotenv()
   |   
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.fail.verify] Failed at verify
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
- [pipeline.fail.implement] Failed at implement: lint:
E701 Multiple statements on one line (colon)
   --> src/intelligent_data_agent/tasks/multi_source_crawl.py:196:35
    |
194 |             matched = _match_keywords(it.title, keywords)
195 |     
- [pipeline.fail.implement] Failed at implement: lint:
E701 Multiple statements on one line (colon)
   --> src/intelligent_data_agent/tasks/multi_source_crawl.py:201:35
    |
199 |             matched = _match_keywords(it.title, keywords)
200 |     
- [pipeline.pass.deliver] Success
- [pipeline.pass.deliver] Success
