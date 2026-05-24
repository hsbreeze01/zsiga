# Spec: SRE Artifacts and Learnings

## ADDED Requirements

### Requirement: SRE Lesson Recording on Success

The SRE pipeline SHALL expose a `record_sre_lesson(result, intent)` function that, after a successful SRE execution (where `result.success is True` and all 5 phases completed), calls `record_lesson()` with `pattern_key == "sre.success"` and `source == "sre_pipeline"`.

#### Scenario: Successful SRE run records success lesson

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::record_sre_lesson
- **Given** a mock result with `success=True` and all 5 phases completed
- **When** `record_sre_lesson(result, "restart nginx service")` is called with `record_lesson` patched
- **Then** `record_lesson` SHALL be called once with `pattern_key="sre.success"` and `source="sre_pipeline"`

---

### Requirement: SRE Lesson Recording on Failure

The `record_sre_lesson()` function SHALL record a failure lesson when `result.success is False`. It MUST call `record_lesson()` with `pattern_key == "sre.failure"` and `source == "sre_pipeline"`.

#### Scenario: Failed SRE run records failure lesson

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::record_sre_lesson
- **Given** a mock result with `success=False` and partial phases completed
- **When** `record_sre_lesson(result, "restart nginx service")` is called with `record_lesson` patched
- **Then** `record_lesson` SHALL be called once with `pattern_key="sre.failure"` and `source="sre_pipeline"`

---

### Requirement: No Git Commit from SRE Pipeline

The SRE pipeline SHALL NOT produce any git commits as part of its execution. Artifacts are limited to `execution_report.md` and learnings appended to `learnings.jsonl`.

#### Scenario: SRE pipeline does not create git commits

- **testable**: false
- **Given** a completed SRE pipeline run
- **When** checking git status
- **Then** there SHALL be no new commits created by the SRE pipeline
