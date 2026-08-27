# harness-runner-pytest

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin captures call-phase reports

`_HarnessCollectorPlugin.pytest_runtest_logreport` SHALL only process reports
whose `when` attribute equals `"call"`. Reports with `when` equal to
`"setup"` or `"teardown"` SHALL be silently ignored.

For call-phase reports the plugin SHALL create a `TestReport` with:
- `name` from `report.nodeid`
- `status` = `"passed"` if `report.passed` is `True`
- `status` = `"failed"` if `report.failed` is `True`
- `status` = `"error"` otherwise
- `duration_s` from `report.duration` (rounded to 6 decimals)
- `message` = `str(report.longrepr)` for failed/error, `""` for passed

#### Scenario: Collector records a passed test

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` instance and a mock report with
  `when="call"`, `passed=True`, `failed=False`, `nodeid="test_a.py::test_ok"`,
  `duration=0.05`, `longrepr=None`
- **When** `pytest_runtest_logreport` is called with the mock report
- **Then** `plugin.reports` SHALL contain exactly one `TestReport` with
  `status="passed"`, `name="test_a.py::test_ok"`, and `message=""`

#### Scenario: Collector records a failed test with longrepr

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` instance and a mock report with
  `when="call"`, `passed=False`, `failed=True`, `nodeid="test_b.py::test_fail"`,
  `duration=0.12`, `longrepr="AssertionError: assert False"`
- **When** `pytest_runtest_logreport` is called with the mock report
- **Then** `plugin.reports[0].status` SHALL equal `"failed"` and
  `plugin.reports[0].message` SHALL equal `"AssertionError: assert False"`

#### Scenario: Collector ignores setup-phase reports

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` instance and a mock report with
  `when="setup"`
- **When** `pytest_runtest_logreport` is called with the mock report
- **Then** `plugin.reports` SHALL be empty

### Requirement: _HarnessCollectorPlugin writes JSONL output

After processing a call-phase report, the plugin SHALL append one JSON line
to `output_path`. Each line SHALL contain keys `name`, `status`,
`duration_s`, `message`, and `timestamp`. The `timestamp` SHALL be an ISO-8601
string in UTC.

#### Scenario: Collector appends valid JSONL for a passed report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl

- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a
  writable file, and a passed call-phase report has been processed
- **When** the JSONL output file is read
- **Then** it SHALL contain exactly one line that parses as valid JSON with
  keys `name`, `status`, `duration_s`, `message`, and `timestamp`; and
  `status` SHALL equal `"passed"`

### Requirement: _HarnessCollectorPlugin records start times

`_HarnessCollectorPlugin.pytest_runtest_logstart` SHALL record the current
time indexed by `nodeid` in the internal `_start_times` dictionary.

#### Scenario: logstart records time for a nodeid

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart

- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_x.py::test_y", None)` is called
- **Then** `plugin._start_times` SHALL contain key `"test_x.py::test_y"` with
  a positive float value

### Requirement: HarnessRunner.run_pytest delegates to pytest.main

`HarnessRunner.run_pytest` SHALL construct a pytest argument list consisting
of the provided `test_paths`, `"-p"`, `"no:cacheprovider"`, and
`"--tb=short"`. It SHALL pass this list together with a
`_HarnessCollectorPlugin` instance as a plugin to `pytest.main`. It SHALL
return the plugin's `reports` list.

#### Scenario: run_pytest passes correct arguments to pytest.main

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a `HarnessRunner` and `pytest.main` is mocked
- **When** `run_pytest(["tests/test_foo.py"])` is called
- **Then** `pytest.main` SHALL be called once with args containing
  `"tests/test_foo.py"`, `"-p"`, `"no:cacheprovider"`, and `"--tb=short"`

#### Scenario: run_pytest returns plugin reports

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a `HarnessRunner` and `pytest.main` is mocked to return `0`
- **When** `run_pytest(["tests/test_sample.py"])` is called
- **Then** the return value SHALL be a list (from `plugin.reports`)
