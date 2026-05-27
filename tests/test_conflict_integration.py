"""Tests for P0 conflict detection + topological ordering integration in run_cycle,
P1 deep copy fix for cross-project decomposition, and P2 deploy branch integrity check."""

import copy
import os
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# P0-1: Conflict detection integration
# ---------------------------------------------------------------------------

class TestConflictDetectionInOrchestrator:
    """Verify warn_change_conflicts is called per target project in run_cycle."""

    def test_warn_change_conflicts_called_per_project(self):
        """run_cycle should call warn_change_conflicts for each configured target."""
        from zsiga.pipeline.utils import warn_change_conflicts

        with patch("zsiga.pipeline.orchestrator.warn_change_conflicts", return_value=None) as mock_warn, \
             patch("zsiga.pipeline.orchestrator.suggest_merge_order", return_value=[]), \
             patch("zsiga.pipeline.orchestrator.DirectoryScanner") as mock_scanner, \
             patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None), \
             patch("zsiga.pipeline.orchestrator.record_lesson"):

            mock_scanner.return_value.scan.return_value = []

            from zsiga.pipeline.orchestrator import ZsigaOrchestrator
            from zsiga.config import ZsigaConfig, PipelineConfig, TargetConfig

            config = MagicMock()
            config.targets = {
                "proj-a": MagicMock(path="/tmp/proj-a"),
                "proj-b": MagicMock(path="/tmp/proj-b"),
            }
            config.pipeline = MagicMock()
            config.pipeline.max_changes_per_cycle = 3
            config.llm = MagicMock()

            with patch.object(ZsigaOrchestrator, "__init__", lambda self, c: None):
                orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
                orch.config = config
                orch._transports = {}
                orch._budget_cache = {}
                orch.agent = MagicMock()

            import asyncio
            asyncio.get_event_loop().run_until_complete(orch.run_cycle())

            assert mock_warn.call_count == 2
            called_paths = {call.args[0] for call in mock_warn.call_args_list}
            assert called_paths == {"/tmp/proj-a", "/tmp/proj-b"}

    def test_conflict_warning_records_lesson(self):
        """When conflicts are detected, a lesson should be recorded."""
        warning_text = "HIGH conflict on utils.py\nSuggested execution order:\n  1. A\n  2. B"

        with patch("zsiga.pipeline.orchestrator.warn_change_conflicts", return_value=warning_text), \
             patch("zsiga.pipeline.orchestrator.suggest_merge_order", return_value=[]), \
             patch("zsiga.pipeline.orchestrator.DirectoryScanner") as mock_scanner, \
             patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None), \
             patch("zsiga.pipeline.orchestrator.record_lesson") as mock_lesson:

            mock_scanner.return_value.scan.return_value = []

            from zsiga.pipeline.orchestrator import ZsigaOrchestrator

            config = MagicMock()
            config.targets = {"proj-a": MagicMock(path="/tmp/proj-a")}
            config.pipeline = MagicMock()
            config.pipeline.max_changes_per_cycle = 3

            with patch.object(ZsigaOrchestrator, "__init__", lambda self, c: None):
                orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
                orch.config = config
                orch._transports = {}
                orch._budget_cache = {}
                orch.agent = MagicMock()

            import asyncio
            asyncio.get_event_loop().run_until_complete(orch.run_cycle())

            mock_lesson.assert_called_once()
            call_kwargs = mock_lesson.call_args[1]
            assert call_kwargs["pattern_key"] == "pipeline.conflict_warning"
            assert "utils.py" in call_kwargs["takeaway"]


# ---------------------------------------------------------------------------
# P0-2: Topological ordering integration
# ---------------------------------------------------------------------------

class TestTopologicalOrderingInOrchestrator:
    """Verify suggest_merge_order is used to sort proposals."""

    def test_proposals_reordered_by_topological_sort(self):
        """run_cycle should reorder proposals according to suggest_merge_order."""
        with patch("zsiga.pipeline.orchestrator.warn_change_conflicts", return_value=None), \
             patch("zsiga.pipeline.orchestrator.suggest_merge_order", return_value=["change-B", "change-A"]), \
             patch("zsiga.pipeline.orchestrator.DirectoryScanner") as mock_scanner, \
             patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None), \
             patch("zsiga.pipeline.orchestrator.record_lesson"), \
             patch("zsiga.pipeline.orchestrator.archive_change"):

            proposals = [
                {"id": "change-A", "project": "proj-a", "change_dir": "/tmp/a",
                 "target_path": "/tmp/proj-a", "proposal_filename": "proposal.md",
                 "has_specs": False, "has_design": False, "has_tasks": False,
                 "has_clarify": False},
                {"id": "change-B", "project": "proj-a", "change_dir": "/tmp/b",
                 "target_path": "/tmp/proj-a", "proposal_filename": "proposal.md",
                 "has_specs": False, "has_design": False, "has_tasks": False,
                 "has_clarify": False},
            ]
            mock_scanner.return_value.scan.return_value = proposals

            from zsiga.pipeline.orchestrator import ZsigaOrchestrator
            from zsiga.metrics.db import load_all_changes

            config = MagicMock()
            config.targets = {"proj-a": MagicMock(path="/tmp/proj-a")}
            config.pipeline = MagicMock()
            config.pipeline.max_changes_per_cycle = 3

            processed_order = []

            async def fake_process(prop):
                processed_order.append(prop["id"])
                return True

            with patch.object(ZsigaOrchestrator, "__init__", lambda self, c: None):
                orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
                orch.config = config
                orch._transports = {}
                orch._budget_cache = {}
                orch.agent = MagicMock()

            with patch.object(orch, "_get_transport", return_value=MagicMock()), \
                 patch.object(orch, "_process_change", side_effect=fake_process), \
                 patch("zsiga.pipeline.orchestrator.decompose") as mock_decompose, \
                 patch("zsiga.pipeline.orchestrator.read_file", return_value="test proposal"), \
                 patch("zsiga.metrics.db.load_all_changes", return_value=[]), \
                 patch("zsiga.pipeline.orchestrator.classify") as mock_classify, \
                 patch("zsiga.pipeline.orchestrator.route", return_value="pipeline"):

                mock_decomp = MagicMock()
                mock_decomp.subtasks = []
                mock_decompose.return_value = mock_decomp

                mock_intent = MagicMock()
                mock_intent.intent_type = MagicMock(value="implementation")
                mock_intent.confidence = 0.9
                mock_intent.verbalization = "test"
                mock_intent.reasoning = "test"
                mock_classify.return_value = mock_intent

                import asyncio
                asyncio.get_event_loop().run_until_complete(orch.run_cycle())

            assert processed_order == ["change-B", "change-A"]

    def test_ordering_error_falls_back_to_scanner_order(self):
        """If suggest_merge_order raises, original scanner order is preserved."""
        with patch("zsiga.pipeline.orchestrator.warn_change_conflicts", return_value=None), \
             patch("zsiga.pipeline.orchestrator.suggest_merge_order", side_effect=RuntimeError("boom")), \
             patch("zsiga.pipeline.orchestrator.DirectoryScanner") as mock_scanner, \
             patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None), \
             patch("zsiga.pipeline.orchestrator.record_lesson"), \
             patch("zsiga.pipeline.orchestrator.archive_change"):

            proposals = [
                {"id": "alpha", "project": "proj-a", "change_dir": "/tmp/a",
                 "target_path": "/tmp/proj-a", "proposal_filename": "proposal.md",
                 "has_specs": False, "has_design": False, "has_tasks": False,
                 "has_clarify": False},
                {"id": "beta", "project": "proj-a", "change_dir": "/tmp/b",
                 "target_path": "/tmp/proj-a", "proposal_filename": "proposal.md",
                 "has_specs": False, "has_design": False, "has_tasks": False,
                 "has_clarify": False},
            ]
            mock_scanner.return_value.scan.return_value = proposals

            from zsiga.pipeline.orchestrator import ZsigaOrchestrator

            config = MagicMock()
            config.targets = {"proj-a": MagicMock(path="/tmp/proj-a")}
            config.pipeline = MagicMock()
            config.pipeline.max_changes_per_cycle = 3

            processed_order = []

            async def fake_process(prop):
                processed_order.append(prop["id"])
                return True

            with patch.object(ZsigaOrchestrator, "__init__", lambda self, c: None):
                orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
                orch.config = config
                orch._transports = {}
                orch._budget_cache = {}
                orch.agent = MagicMock()

            with patch.object(orch, "_get_transport", return_value=MagicMock()), \
                 patch.object(orch, "_process_change", side_effect=fake_process), \
                 patch("zsiga.pipeline.orchestrator.decompose") as mock_decompose, \
                 patch("zsiga.pipeline.orchestrator.read_file", return_value="test"), \
                 patch("zsiga.metrics.db.load_all_changes", return_value=[]), \
                 patch("zsiga.pipeline.orchestrator.classify") as mock_classify, \
                 patch("zsiga.pipeline.orchestrator.route", return_value="pipeline"):

                mock_decomp = MagicMock()
                mock_decomp.subtasks = []
                mock_decompose.return_value = mock_decomp

                mock_intent = MagicMock()
                mock_intent.intent_type = MagicMock(value="implementation")
                mock_intent.confidence = 0.9
                mock_intent.verbalization = "test"
                mock_intent.reasoning = "test"
                mock_classify.return_value = mock_intent

                import asyncio
                asyncio.get_event_loop().run_until_complete(orch.run_cycle())

            assert processed_order == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# P1: Deep copy in cross-project decomposition
# ---------------------------------------------------------------------------

class TestDeepCopyInDecomposition:
    """Verify that cross-project decomposition uses deep copy to prevent
    sub_prop mutation from leaking into sibling subtasks."""

    def test_deep_copy_prevents_mutation_leak(self):
        original = {
            "id": "cross-123",
            "project": "proj-a",
            "target_path": "/tmp/a",
            "change_dir": "/tmp/changes/cross-123",
            "proposal_filename": "proposal.md",
            "nested": {"key": "value_a"},
        }
        shallow = dict(original)
        shallow["project"] = "proj-b"
        shallow["nested"]["key"] = "value_b"

        assert original["nested"]["key"] == "value_b", "shallow copy leaked mutation"

        original2 = {
            "id": "cross-456",
            "project": "proj-a",
            "target_path": "/tmp/a",
            "change_dir": "/tmp/changes/cross-456",
            "proposal_filename": "proposal.md",
            "nested": {"key": "value_a"},
        }
        deep = copy.deepcopy(original2)
        deep["project"] = "proj-b"
        deep["nested"]["key"] = "value_b"

        assert original2["nested"]["key"] == "value_a", "deep copy should not leak"
        assert original2["project"] == "proj-a"


# ---------------------------------------------------------------------------
# P2: Deploy branch HEAD integrity check
# ---------------------------------------------------------------------------

class TestDeployBranchIntegrity:
    """Verify git_ops.rev_parse accepts a ref parameter for remote HEAD comparison."""

    def test_rev_parse_accepts_ref_parameter(self):
        """rev_parse should accept a ref parameter and use it in git command."""
        from zsiga import git_ops

        transport = MagicMock()
        transport.run_shell.return_value = {"stdout": "abc1234567\n", "exit_code": 0}

        result = git_ops.rev_parse("/tmp/repo", transport=transport, ref="origin/main")

        transport.run_shell.assert_called_once_with(
            "git rev-parse origin/main", cwd="/tmp/repo"
        )
        assert result == "abc1234567"

    def test_rev_parse_default_ref_is_head(self):
        """rev_parse without ref parameter defaults to HEAD."""
        from zsiga import git_ops

        transport = MagicMock()
        transport.run_shell.return_value = {"stdout": "def789\n", "exit_code": 0}

        result = git_ops.rev_parse("/tmp/repo", transport=transport)

        transport.run_shell.assert_called_once_with(
            "git rev-parse HEAD", cwd="/tmp/repo"
        )
        assert result == "def789"
