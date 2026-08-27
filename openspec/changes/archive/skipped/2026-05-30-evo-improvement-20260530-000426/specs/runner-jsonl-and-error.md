# runner-jsonl-and-error

## ADDED Requirements

### Requirement: _append_jsonl writes valid JSON lines

`_HarnessCollectorPlugin._append_jsonl()` SHALL append one JSON object per call
to the configured output file. Each line SHALL contain the keys `"name"`, `"status"`,
`"duration_s"`, `"message"`, and `"timestamp"`. Subsequent calls SHALL append
without overwriting previous lines.

### Requirement: add_harness_error records an error report

`_HarnessCollectorPlugin.add_harness_error()` SHALL create a `TestReport` with
`name="__harness__::pytest"`, `status="error"`, `duration_s=0.0`, and the given
message. It SHALL also append this report to the JSONL output file.

#### Scenario: _append_jsonl writes one valid JSON line per call

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file, and a `TestReport(name="t1", status="passed", duration_s=0.01, message="")`
- **When** `plugin._append_jsonl(report)` is called
- **Then** the output file contains exactly 1 line, which parses as JSON with keys `"name"`, `"status"`, `"duration_s"`, `"message"`, `"timestamp"` where `"name" == "t1"` and `"status" == "passed"`

#### Scenario: _append_jsonl appends without overwriting previous lines

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file that already contains 1 JSON line, and a second `TestReport(name="t2", status="failed", duration_s=0.5, message="oops")`
- **When** `plugin._append_jsonl(report)` is called
- **Then** the output file contains exactly 2 lines, both valid JSON; the second line has `"name" == "t2"` and `"status" == "failed"`

#### Scenario: add_harness_error creates error report with correct fields

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.add_harness_error
- **Given** a `_HarnessCollectorPlugin` instance with empty `reports` and `output_path` pointing to a temporary file
- **When** `plugin.add_harness_error("something went wrong")` is called
- **Then** `plugin.reports` has length 1, the report has `name == "__harness__::pytest"`, `status == "error"`, `duration_s == 0.0`, and `message == "something went wrong"`, and the JSONL file contains 1 line with `"status" == "error"`
