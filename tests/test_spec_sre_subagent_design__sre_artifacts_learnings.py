"""Tests for SRE artifacts and learnings spec."""
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Scenario: Successful SRE run records success lesson
# ---------------------------------------------------------------------------
def test_successful_sre_records_success_lesson():
    from zsiga.pipeline.sre_pipeline import record_sre_lesson

    result = MagicMock()
    result.success = True
    result.phases_completed = ["DIAGNOSE", "PLAN", "EXECUTE", "VERIFY", "REPORT"]
    result.commands_executed = ["systemctl restart nginx"]

    with patch("zsiga.pipeline.sre_pipeline.record_lesson") as mock_record:
        record_sre_lesson(result, "restart nginx service")
        mock_record.assert_called_once()
        call_kwargs = mock_record.call_args
        # Check pattern_key and source
        if call_kwargs.kwargs:
            assert call_kwargs.kwargs.get("pattern_key") == "sre.success"
            assert call_kwargs.kwargs.get("source") == "sre_pipeline"
        else:
            # positional args
            kw = call_kwargs[1] if len(call_kwargs) > 1 else {}
            assert kw.get("pattern_key", call_kwargs[0][3] if len(call_kwargs[0]) > 3 else "") == "sre.success"


# ---------------------------------------------------------------------------
# Scenario: Failed SRE run records failure lesson
# ---------------------------------------------------------------------------
def test_failed_sre_records_failure_lesson():
    from zsiga.pipeline.sre_pipeline import record_sre_lesson

    result = MagicMock()
    result.success = False
    result.phases_completed = ["DIAGNOSE", "PLAN"]
    result.commands_executed = []

    with patch("zsiga.pipeline.sre_pipeline.record_lesson") as mock_record:
        record_sre_lesson(result, "restart nginx service")
        mock_record.assert_called_once()
        call_kwargs = mock_record.call_args
        if call_kwargs.kwargs:
            assert call_kwargs.kwargs.get("pattern_key") == "sre.failure"
            assert call_kwargs.kwargs.get("source") == "sre_pipeline"
        else:
            kw = call_kwargs[1] if len(call_kwargs) > 1 else {}
            assert kw.get("pattern_key", call_kwargs[0][3] if len(call_kwargs[0]) > 3 else "") == "sre.failure"
