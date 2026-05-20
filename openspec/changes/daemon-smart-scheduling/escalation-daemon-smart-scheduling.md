# 诊断报告: daemon-smart-scheduling
总尝试次数: 1
需要人工介入: 否

## 失败记录
- 第1次 (implement): lint:
F841 Local variable `sig` is assigned to but never used
   --> tests/test_daemon_scheduling.py:361:9
    |
359 |         from zsiga.pipeline.orchestrator import ZsigaOrchestrator
360 |         import inspect
361 |         sig = inspect.signature(ZsigaOrchestrator.run_cycle)
    |         ^^^
362 |         # Verify the method exists and is async
363 |         assert inspect.iscoroutinefunction(ZsigaOrchestrator.run_cycle)
    |
help: Remove assignment to unused variable `sig`
Found 1 error.
No fixes available (1 hidden fix can be enabled with the `--unsafe-fixes` option).
tests:
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/zsiga/repo
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 9 items

tests/test_daemon_scheduling.py .....F

=================================== FAILURES ===================================
____________ TestSmartSchedulingSafetyValve.test_cooldown_triggered ____________
tests/test_daemon_scheduling.py:296: in test_cooldown_triggered
    assert total_slept == 600 + 300
E   assert 600 == (600 + 300)
----------------------------- Captured stdout call -----------------------------
⚡ zsiga daemon started (PID 859800)
   Cycle interval: 8h
   Idle poll: 5min
   Lock: /home/zsiga/repo/data/lock.pid

============================================================
zsiga daemon — cycle #1 @ 2026-05-20 08:02:27
============================================================

  ⚡ Processed 1 changes — immediate next cycle

============================================================
zsiga daemon — cycle #2 @ 2026-05-20 08:02:27
============================================================

  ⚡ Processed 1 changes — immediate next cycle

============================================================
zsiga daemon — cycle #3 @ 2026-05-20 08:02:27
============================================================

  ⚠️ Safety valve: 3 consecutive busy cycles, cooling down for 10 minutes

============================================================
zsiga daemon — cycle #4 @ 2026-05-20 08:02:27
============================================================

⚡ zsiga daemon stopped (ran 4 cycles)
=========================== short test summary info ============================
FAILED tests/test_daemon_scheduling.py::TestSmartSchedulingSafetyValve::test_cooldown_triggered
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
========================= 1 failed, 5 passed in 1.05s ==========================
 [策略: same]

## 根因假设
所有失败发生在同一阶段 (implement)，可能是该阶段的系统性问题

## 建议操作
尝试不同策略