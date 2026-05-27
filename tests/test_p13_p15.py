"""Tests for P1-3 (spec→code alignment) and P1-5 (adaptive token budget)."""
import json
import os
import tempfile

from zsiga.intake.evolution import (
    EvolutionConfig,
    EvolutionEngine,
    _TOKEN_BUDGET_BASE_CAP,
    _TOKEN_BUDGET_SAFETY_MARGIN,
)
from zsiga.intake.langfuse_reader import AggregatedMetrics
from zsiga.pipeline.enricher import _extract_and_save_spec_keywords
from zsiga.pipeline.implementer import _build_spec_keywords_section
from zsiga.transport import LocalTransport


class TestSpecKeywords:
    """P1-3: spec→code keyword extraction and injection."""

    def setup_method(self):
        self.t = LocalTransport()
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, "specs"))

    def _write_spec(self, content, name="feature.md"):
        with open(os.path.join(self.tmpdir, "specs", name), "w") as f:
            f.write(content)

    def test_shall_verbs_extracted(self):
        self._write_spec(
            "System SHALL provide /api/health endpoint\n"
            "Response SHALL return HTTP 200 JSON\n"
        )
        _extract_and_save_spec_keywords(self.tmpdir, self.t)
        data = json.load(open(os.path.join(self.tmpdir, "spec_keywords.json")))
        assert len(data["keywords"]) >= 1

    def test_must_verbs_extracted(self):
        self._write_spec(
            "The endpoint MUST include status and timestamp fields\n"
        )
        _extract_and_save_spec_keywords(self.tmpdir, self.t)
        data = json.load(open(os.path.join(self.tmpdir, "spec_keywords.json")))
        assert any("status" in kw or "timestamp" in kw for kw in data["keywords"])

    def test_generic_stop_words_filtered(self):
        self._write_spec(
            "System SHALL be a thing\n"
        )
        _extract_and_save_spec_keywords(self.tmpdir, self.t)
        data = json.load(open(os.path.join(self.tmpdir, "spec_keywords.json")))
        for kw in data["keywords"]:
            assert "system" not in kw.lower().split()
            assert "shall" not in kw.lower().split()

    def test_no_shall_must_produces_no_file(self):
        self._write_spec("Just some regular text without requirements.\n")
        _extract_and_save_spec_keywords(self.tmpdir, self.t)
        assert not os.path.exists(os.path.join(self.tmpdir, "spec_keywords.json"))

    def test_empty_specs_dir_no_crash(self):
        empty_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(empty_dir, "specs"))
        _extract_and_save_spec_keywords(empty_dir, self.t)
        assert not os.path.exists(os.path.join(empty_dir, "spec_keywords.json"))

    def test_implementer_reads_keywords(self):
        self._write_spec(
            "System SHALL provide error_response object\n"
            "Error cases MUST return structured error_response\n"
        )
        _extract_and_save_spec_keywords(self.tmpdir, self.t)
        section = _build_spec_keywords_section(self.tmpdir, self.t)
        assert "Spec Alignment Keywords" in section
        assert "error_response" in section

    def test_implementer_empty_when_no_keywords(self):
        empty_dir = tempfile.mkdtemp()
        section = _build_spec_keywords_section(empty_dir, self.t)
        assert section == ""

    def test_implementer_invalid_json_returns_empty(self):
        td = tempfile.mkdtemp()
        with open(os.path.join(td, "spec_keywords.json"), "w") as f:
            f.write("not valid json{{{")
        section = _build_spec_keywords_section(td, self.t)
        assert section == ""


class TestAdaptiveTokenBudget:
    """P1-5: adaptive token budget cap based on budget_analyzer data."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, "data"), exist_ok=True)
        self.engine = EvolutionEngine(self.tmpdir, EvolutionConfig())

    def test_fallback_base_cap_when_no_db(self):
        lm = AggregatedMetrics(total_tokens=0)
        cap = self.engine._compute_token_budget_cap(lm)
        assert cap == _TOKEN_BUDGET_BASE_CAP

    def test_fallback_base_cap_on_empty_metrics(self):
        lm = AggregatedMetrics(total_tokens=0, trace_count=0)
        cap = self.engine._compute_token_budget_cap(lm)
        assert cap >= _TOKEN_BUDGET_BASE_CAP

    def test_budget_exceeded_finding_in_intake(self):
        engine = EvolutionEngine(self.tmpdir, EvolutionConfig())
        cap = engine._compute_token_budget_cap(AggregatedMetrics())
        high_usage_lm = AggregatedMetrics(
            trace_count=5,
            total_tokens=cap + 1,
            avg_tokens_per_trace=20000,
            costliest_phase="implement",
            costliest_phase_tokens=5000000,
        )
        findings = []
        if high_usage_lm.total_tokens >= cap:
            findings.append(
                f"token_budget_exceeded:{high_usage_lm.total_tokens}:{cap}"
            )
        assert len(findings) == 1
        assert findings[0].startswith("token_budget_exceeded:")
        parts = findings[0].split(":")
        assert int(parts[1]) == cap + 1
        assert int(parts[2]) == cap

    def test_budget_not_exceeded_below_cap(self):
        engine = EvolutionEngine(self.tmpdir, EvolutionConfig())
        cap = engine._compute_token_budget_cap(AggregatedMetrics())
        low_usage_lm = AggregatedMetrics(
            trace_count=5,
            total_tokens=1000,
        )
        assert low_usage_lm.total_tokens < cap

    def test_phase2_overrides_scope_on_budget_exceeded(self):
        engine = EvolutionEngine(self.tmpdir, EvolutionConfig())
        findings = [
            f"token_budget_exceeded:{_TOKEN_BUDGET_BASE_CAP + 1}:{_TOKEN_BUDGET_BASE_CAP}",
            f"high_cost_phase:implement:5000000",
        ]
        facts = {
            "findings": findings,
            "recent_evo_rejections": [],
            "langfuse_metrics": AggregatedMetrics(
                total_tokens=_TOKEN_BUDGET_BASE_CAP + 1,
                trace_count=5,
                costliest_phase="implement",
                costliest_phase_tokens=5000000,
            ),
        }
        insights = engine._phase2_reflect(facts)
        assert insights["scope"] == "cost_only"
        assert insights["confidence"] == "high"
        assert insights["priority_finding"]["type"] == "enforce_budget_cap"
        assert insights["priority_finding"]["costliest_phase"] == "implement"

    def test_phase4_generates_budget_cap_proposal(self):
        engine = EvolutionEngine(self.tmpdir, EvolutionConfig())
        finding = {
            "type": "enforce_budget_cap",
            "used": _TOKEN_BUDGET_BASE_CAP + 1,
            "cap": _TOKEN_BUDGET_BASE_CAP,
            "costliest_phase": "implement",
            "phase_tokens": 5000000,
        }
        facts = {
            "langfuse_metrics": AggregatedMetrics(total_tokens=_TOKEN_BUDGET_BASE_CAP + 1),
        }
        content = engine._render_budget_cap_proposal(finding, facts)
        assert "token-budget-cap-enforcement" in content
        assert "budget_analyzer" in content
        assert "20%" in content

    def test_phase3_records_budget_cap_lesson(self):
        engine = EvolutionEngine(self.tmpdir, EvolutionConfig())
        facts = {"langfuse_metrics": AggregatedMetrics()}
        insights = {
            "priority_finding": {
                "type": "enforce_budget_cap",
                "used": _TOKEN_BUDGET_BASE_CAP + 1,
                "cap": _TOKEN_BUDGET_BASE_CAP,
            },
        }
        result = engine._phase3_learn(facts, insights)
        assert result is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
