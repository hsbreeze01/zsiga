# runner-plugin-hooks

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin hook event recording

`_HarnessCollectorPlugin` SHALL record test start times on `pytest_runtest_logstart`
and produce `TestReport` objects on `pytest_runtest_logreport` for the `"call"` phase only.

- `pytest_runtest_logstart(nodeid, location)` SHALL store the start time indexed by `nodeid`.
- `pytest_runtest_logreport(report)` SHALL ignore reports where `report.when != "call"`.
- For `"call"` phase reports, `pytest_runtest_logreport` SHALL append exactly one
  `TestReport` to `self.reports` with `status` derived from `report.passed`/`report.failed`.
- `pytest_collectreport` SHALL create a `TestReport` with `status="error"` when
  `report.failed` is `True` during collection.

#### Scenario: pytest_runtest_logstart records start time by nodeid

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance with an empty `_start_times` dict
- **When** `plugin.pytest_runtest_logstart("tests/test_x.py::test_a", ("test_x.py", 1, "test_a"))` is called
- **Then** `plugin._start_times["tests/test_x.py::test_a"]` is a `float` greater than `0`

#### Scenario: pytest_runtest_logreport ignores setup and teardown phases

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with empty `reports` list
- **When** `plugin.pytest_runtest_logreport(report)` is called with a mock report where `report.when == "setup"` and `report.passed is True`
- **Then** `plugin.reports` remains empty (length 0)

#### Scenario: pytest_runtest_logreport records call-phase passed result

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with empty `reports` list
- **When** `plugin.pytest_runtest_logreport(report)` is called with a mock report where `report.when == "call"`, `report.passed is True`, `report.failed is False`, `report.nodeid == "test_x.py::test_ok"`, `report.duration == 0.05`, and `report.longrepr is None`
- **Then** `plugin.reports` has length 1 and `plugin.reports[0].status == "passed"` and `plugin.reports[0].name == "test_x.py::test_ok"`

#### Scenario: pytest_runtest_logreport records call-phase failed result with message

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with empty `reports` list
- **When** `plugin.pytest_runtest_logreport(report)` is called with a mock report where `report.when == "call"`, `report.passed is False`, `report.failed is True`, `report.nodeid == "test_x.py::test_bad"`, `report.duration == 0.1`, and `report.longrepr == "AssertionError: assert False"`
- **Then** `plugin.reports` has length 1 and `plugin.reports[0].status == "failed"` and `plugin.reports[0].message == "AssertionError: assert False"`
