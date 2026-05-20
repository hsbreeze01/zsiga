"""Tests for _render_proposal_queue() in the dashboard."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zsiga.metrics.dashboard import _render_proposal_queue

# The real base directory the dashboard module reads daemon_state from
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DAEMON_STATE = _REPO_ROOT / "data" / "daemon_state.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proposal_dir(base: Path, name: str, proposal_text: str = ""):
    """Create a minimal proposal directory structure under openspec/changes/."""
    change_dir = base / "openspec" / "changes" / name
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "proposal.md").write_text(proposal_text, encoding="utf-8")
    # Create specs dir so scanner sees it as valid
    (change_dir / "specs").mkdir(exist_ok=True)


def _make_target(path: Path):
    """Build a TargetConfig-like object."""
    tc = MagicMock()
    tc.path = str(path)
    tc.ssh = None
    return tc


@pytest.fixture()
def preserve_daemon_state():
    """Save and restore daemon_state.json around the test."""
    original = None
    if _DAEMON_STATE.exists():
        original = _DAEMON_STATE.read_text(encoding="utf-8")
    yield
    if original is not None:
        _DAEMON_STATE.write_text(original, encoding="utf-8")
    elif _DAEMON_STATE.exists():
        _DAEMON_STATE.unlink()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEmptyQueue:
    """Scenario: no proposals in queue → idle message."""

    def test_no_targets_returns_idle(self):
        """No target projects → queue empty message."""
        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()
        assert "📋 Proposal Queue" in html
        assert "Queue empty — idle polling" in html

    def test_targets_no_proposals_returns_idle(self, tmp_path):
        """Targets exist but no proposal dirs → queue empty message."""
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        tc = _make_target(target_dir)

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()
        assert "Queue empty — idle polling" in html


class TestMultiProposalTable:
    """Scenario: multiple proposals queued across projects."""

    def test_three_proposals_show_three_rows(self, tmp_path):
        """Two proposals in project A, one in project B → 3 table rows."""
        factory = tmp_path / "factory"
        compass = tmp_path / "compass"
        factory.mkdir()
        compass.mkdir()

        _make_proposal_dir(factory, "feat-1", "# Add auth\nBody")
        _make_proposal_dir(factory, "feat-2", "# Fix bug\nBody")
        _make_proposal_dir(compass, "feat-3", "# Refactor\nBody")

        tc_factory = _make_target(factory)
        tc_compass = _make_target(compass)

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc_factory, "compass": tc_compass}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        # Should have 3 data table rows (plus 1 header row)
        assert html.count("<tr") == 4  # 1 header + 3 data
        assert "feat-1" in html
        assert "feat-2" in html
        assert "feat-3" in html
        assert "factory" in html
        assert "compass" in html

    def test_table_has_correct_columns(self, tmp_path):
        """Table header has Proposal, Project, Summary columns."""
        factory = tmp_path / "factory"
        factory.mkdir()
        _make_proposal_dir(factory, "my-feature", "# Cool feature\n")

        tc = _make_target(factory)

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        assert "<th>Proposal</th>" in html
        assert "<th>Project</th>" in html
        assert "<th>Summary</th>" in html


class TestCurrentChangeHighlight:
    """Scenario: daemon actively processing a proposal."""

    def test_active_change_has_highlight(self, tmp_path, preserve_daemon_state):
        """Current change row gets amber left-border highlight + phase badge."""
        factory = tmp_path / "factory"
        factory.mkdir()
        _make_proposal_dir(factory, "add-auth", "# Add auth\n")

        tc = _make_target(factory)

        # Write daemon_state.json with current_change matching the proposal
        state = {
            "current_change": "add-auth",
            "current_phase": "implement",
        }
        _DAEMON_STATE.parent.mkdir(parents=True, exist_ok=True)
        _DAEMON_STATE.write_text(json.dumps(state), encoding="utf-8")

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        # The active row should have the amber border
        assert "border-left:3px solid #f59e0b" in html
        assert "implement" in html

    def test_no_current_change_no_highlight(self, tmp_path, preserve_daemon_state):
        """Daemon idle → no rows highlighted, no phase badges."""
        factory = tmp_path / "factory"
        factory.mkdir()
        _make_proposal_dir(factory, "add-auth", "# Add auth\n")

        tc = _make_target(factory)

        # Write daemon_state.json with null current_change
        state = {"current_change": None, "current_phase": None}
        _DAEMON_STATE.write_text(json.dumps(state), encoding="utf-8")

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        assert "border-left:3px solid #f59e0b" not in html


class TestProposalSummaryExtraction:
    """Scenario: proposal summary extracted from first heading line."""

    def test_heading_extracted(self, tmp_path):
        """First # heading becomes the summary text."""
        factory = tmp_path / "factory"
        factory.mkdir()
        _make_proposal_dir(
            factory, "my-feature", "# Cool Feature Proposal\nSome details\n"
        )

        tc = _make_target(factory)

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        assert "Cool Feature Proposal" in html

    def test_missing_heading_shows_dash(self, tmp_path):
        """No # heading line → summary shows dash."""
        factory = tmp_path / "factory"
        factory.mkdir()
        _make_proposal_dir(factory, "no-heading", "Just some text\nNo heading\n")

        tc = _make_target(factory)

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        # The summary for this proposal should be "—"
        assert "<td>—</td>" in html

    def test_missing_proposal_md_not_scanned(self, tmp_path):
        """Dirs without proposal.md are skipped by scanner → empty queue."""
        factory = tmp_path / "factory"
        factory.mkdir()
        change_dir = factory / "openspec" / "changes" / "no-file"
        change_dir.mkdir(parents=True)
        (change_dir / "specs").mkdir()

        tc = _make_target(factory)

        with patch("zsiga.config.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.targets = {"factory": tc}
            mock_cfg.return_value = cfg
            html = _render_proposal_queue()

        assert "Queue empty — idle polling" in html


class TestConfigLoadFailure:
    """Scenario: load_config raises → graceful fallback."""

    def test_config_error_returns_idle(self):
        """If load_config fails, return idle message."""
        with patch(
            "zsiga.config.load_config",
            side_effect=FileNotFoundError("no config"),
        ):
            html = _render_proposal_queue()
        assert "Queue empty — idle polling" in html
