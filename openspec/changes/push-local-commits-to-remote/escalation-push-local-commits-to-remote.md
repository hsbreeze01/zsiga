# 诊断报告: push-local-commits-to-remote
总尝试次数: 2
需要人工介入: 否

## 失败记录
- 第1次 (implement): tests:
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/zsiga/repo
configfile: pyproject.toml
plugins: timeout-2.4.0, anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 8 items

tests/test_spec_push_local_commits_to_remote__push_sync.py F

=================================== FAILURES ===================================
____________________ test_preflight_working_directory_clean ____________________
tests/test_spec_push_local_commits_to_remote__push_sync.py:39: in test_preflight_working_directory_clean
    assert dirty_tracked == [], (
E   AssertionError: Working directory has dirty tracked files before push: ['M tests/test_spec_push_local_commits_to_remote__push_sync.py']
E   assert ['M tests/tes...push_sync.py'] == []
E     
E     Left contains one more item: 'M tests/test_spec_push_local_commits_to_remote__push_sync.py'
E     Use -v to get more diff
=========================== short test summary info ============================
FAILED tests/test_spec_push_local_commits_to_remote__push_sync.py::test_preflight_working_directory_clean
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
============================== 1 failed in 0.06s ===============================
 [策略: same]
- 第2次 (implement): tests:
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/zsiga/repo
configfile: pyproject.toml
plugins: timeout-2.4.0, anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 8 items

tests/test_spec_push_local_commits_to_remote__push_sync.py ..ssssF

=================================== FAILURES ===================================
________________________ test_no_source_files_modified _________________________
tests/test_spec_push_local_commits_to_remote__push_sync.py:144: in test_no_source_files_modified
    assert diff_output == "", (
E   AssertionError: Expected no modified source files, but found:
E     tests/test_spec_push_local_commits_to_remote__push_sync.py
E   assert 'tests/test_s..._push_sync.py' == ''
E     
E     + tests/test_spec_push_local_commits_to_remote__push_sync.py
=========================== short test summary info ============================
FAILED tests/test_spec_push_local_commits_to_remote__push_sync.py::test_no_source_files_modified
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
=================== 1 failed, 2 passed, 4 skipped in 17.00s ====================
 [策略: same]

## 根因假设
所有失败发生在同一阶段 (implement)，可能是该阶段的系统性问题

## 建议操作
尝试不同策略