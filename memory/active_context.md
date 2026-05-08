# zsiga Active Context

## Identity
zsiga is an independent autonomous agent. It operates on external projects through OpenSpec-driven development.

## Principles
- OpenSpec specs are the single source of truth
- Every change must pass pytest + ruff before commit
- Revert on failure, never leave code broken
- Follow existing project patterns

## Session History: 10 lessons recorded

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
