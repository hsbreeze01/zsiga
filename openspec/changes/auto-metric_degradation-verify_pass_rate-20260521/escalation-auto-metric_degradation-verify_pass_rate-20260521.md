# 诊断报告: auto-metric_degradation-verify_pass_rate-20260521
总尝试次数: 1
需要人工介入: 否

## 失败记录
- 第1次 (implement): lint:
F841 Local variable `proposal_queue_section` is assigned to but never used
   --> zsiga/metrics/dashboard.py:377:9
    |
375 |         proposal_queue_section = _render_proposal_queue()
376 |     except Exception:
377 |         proposal_queue_section = ""
    |         ^^^^^^^^^^^^^^^^^^^^^^
378 |     try:
379 |         failure_section = _render_failure_diagnosis()
    |
help: Remove assignment to unused variable `proposal_queue_section`
Found 1 error.
No fixes available (1 hidden fix can be enabled with the `--unsafe-fixes` option).
tests:
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/zsiga/repo
configfile: pyproject.toml
plugins: timeout-2.4.0, anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 37 items

tests/test_spec_fix_learnings_noise_and_inject__cleanup.py F

=================================== FAILURES ===================================
_____ TestRemoveDaemonCycleErrorFromJsonl.test_daemon_cycle_error_removed ______
tests/test_spec_fix_learnings_noise_and_inject__cleanup.py:58: in test_daemon_cycle_error_removed
    from zsiga.memory.learn import clean_noisy_learnings
E   ImportError: cannot import name 'clean_noisy_learnings' from 'zsiga.memory.learn' (/home/zsiga/repo/zsiga/memory/learn.py)
=========================== short test summary info ============================
FAILED tests/test_spec_fix_learnings_noise_and_inject__cleanup.py::TestRemoveDaemonCycleErrorFromJsonl::test_daemon_cycle_error_removed
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
============================== 1 failed in 0.12s ===============================
 [策略: same]

## 根因假设
所有失败发生在同一阶段 (implement)，可能是该阶段的系统性问题

## 建议操作
尝试不同策略