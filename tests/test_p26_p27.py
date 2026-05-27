"""Tests for P2-6 (Langfuse scoring) and P2-7 (success template extraction)."""
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from zsiga.agent.langfuse_shim import score_proposal
from zsiga.pipeline.orchestrator import _extract_success_template
from zsiga.transport import LocalTransport


class TestLangfuseScoring:
    """P2-6: Steward score write-back to Langfuse."""

    def test_score_proposal_no_crash_without_langfuse(self):
        score_proposal(
            change_name="test-change",
            score=10,
            verdict="ACCEPT",
        )

    def test_score_proposal_with_dimensions(self):
        score_proposal(
            change_name="test-change",
            score=8,
            verdict="PUSHBACK",
            dimensions={"feasibility": 2, "scope": 1},
        )

    @patch("zsiga.agent.langfuse_shim._client")
    def test_score_proposal_calls_client(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        from zsiga.agent import langfuse_shim
        langfuse_shim._enabled_cache = True
        langfuse_shim._client_cache = mock_client
        try:
            score_proposal(
                trace_id="trace-123",
                change_name="test-change",
                score=11,
                verdict="ACCEPT",
                dimensions={"feasibility": 2},
            )
            mock_client.score.assert_called_once()
            call_kwargs = mock_client.score.call_args[1]
            assert call_kwargs["value"] == 11
            assert "ACCEPT" in call_kwargs["comment"]
            assert call_kwargs["trace_id"] == "trace-123"
        finally:
            langfuse_shim._enabled_cache = None
            langfuse_shim._client_cache = None

    @patch("zsiga.agent.langfuse_shim._client")
    def test_score_proposal_handles_error(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.score.side_effect = RuntimeError("API error")
        mock_client_fn.return_value = mock_client
        from zsiga.agent import langfuse_shim
        langfuse_shim._enabled_cache = True
        langfuse_shim._client_cache = mock_client
        try:
            score_proposal(change_name="x", score=5, verdict="REJECT")
        finally:
            langfuse_shim._enabled_cache = None
            langfuse_shim._client_cache = None


class TestSuccessTemplateExtraction:
    """P2-7: extract proposal template after DELIVER success."""

    def setup_method(self):
        self.t = LocalTransport()
        self.tmpdir = tempfile.mkdtemp()
        self.change_dir = os.path.join(self.tmpdir, "my-feature")
        os.makedirs(self.change_dir)

    def _write_proposal(self, content):
        with open(os.path.join(self.change_dir, "proposal.md"), "w") as f:
            f.write(content)

    def test_extracts_basic_template(self):
        self._write_proposal(
            "# add-health-check\n\n"
            "## Summary\nAdd /api/health endpoint\n\n"
            "## Acceptance Criteria\n"
            "- [BAC-01] Endpoint returns 200\n"
            "- [BAC-02] Response has status field\n"
            "- [BAC-03] No auth required\n\n"
            "## Scope\n- In scope: health endpoint only\n"
        )
        _extract_success_template(self.change_dir, "add-health-check", self.t)

        templates_dir = os.path.join(self.tmpdir, "..", "memory", "templates")
        templates_dir = os.path.normpath(templates_dir)
        tpl_path = os.path.join(templates_dir, "add-health-check.json")
        assert os.path.exists(tpl_path)
        tpl = json.load(open(tpl_path))
        assert tpl["source"] == "add-health-check"
        assert "health" in tpl["title"]
        assert tpl["acceptance_count"] == 3

    def test_no_template_without_proposal(self):
        _extract_success_template(self.change_dir, "no-proposal", self.t)

        templates_dir = os.path.join(self.tmpdir, "..", "memory", "templates")
        templates_dir = os.path.normpath(templates_dir)
        assert not os.path.exists(os.path.join(templates_dir, "no-proposal.json"))

    def test_no_template_with_empty_title(self):
        parent = tempfile.mkdtemp(prefix="zsiga_tpl_test_")
        change_dir = os.path.join(parent, "empty")
        os.makedirs(change_dir)
        unique_name = "empty-title-noheader-unique-9999"
        with open(os.path.join(change_dir, "proposal.md"), "w") as f:
            f.write("just some text without a proper header")
        _extract_success_template(change_dir, unique_name, self.t)

        templates_dir = os.path.normpath(os.path.join(parent, "..", "memory", "templates"))
        tpl_path = os.path.join(templates_dir, f"{unique_name}.json")
        assert not os.path.exists(tpl_path), f"Template should not exist: {tpl_path}"

    def test_template_includes_scope(self):
        self._write_proposal(
            "# add-metrics\n\n"
            "## Summary\nAdd metrics endpoint\n\n"
            "## Scope\n- In scope: /api/metrics endpoint only\n"
        )
        _extract_success_template(self.change_dir, "add-metrics", self.t)

        templates_dir = os.path.join(self.tmpdir, "..", "memory", "templates")
        templates_dir = os.path.normpath(templates_dir)
        tpl_path = os.path.join(templates_dir, "add-metrics.json")
        tpl = json.load(open(tpl_path))
        assert "metrics" in tpl["scope"].lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
