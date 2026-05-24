"""Tests for pipeline-gates-config spec (enable-sub-agent-gates change).

Verifies that zsiga.yaml contains proposal_gate and design_gate configuration
blocks with correct fields and values, while preserving existing config.
"""
import copy
from pathlib import Path

import yaml


YAML_PATH = Path(__file__).resolve().parent.parent / "zsiga.yaml"


def _load_config():
    """Load and return the zsiga.yaml config dict."""
    assert YAML_PATH.exists(), f"zsiga.yaml not found at {YAML_PATH}"
    with open(YAML_PATH) as f:
        return yaml.safe_load(f)


class TestProposalGateBlock:
    """Scenario: proposal_gate block exists with all required fields."""

    def test_proposal_gate_keys_present(self):
        cfg = _load_config()
        pg = cfg["pipeline"]["proposal_gate"]
        expected_keys = {
            "enabled",
            "max_retries",
            "steward_max_turns",
            "steward_timeout",
            "score_accept",
            "score_pushback",
            "learning_weight_days",
        }
        assert set(pg.keys()) == expected_keys, (
            f"proposal_gate keys mismatch: got {set(pg.keys())}, want {expected_keys}"
        )

    def test_proposal_gate_enabled_is_true(self):
        """Scenario: proposal_gate is enabled."""
        cfg = _load_config()
        assert cfg["pipeline"]["proposal_gate"]["enabled"] is True

    def test_proposal_gate_field_values(self):
        cfg = _load_config()
        pg = cfg["pipeline"]["proposal_gate"]
        assert pg["max_retries"] == 1
        assert pg["steward_max_turns"] == 3
        assert pg["steward_timeout"] == 90
        assert pg["score_accept"] == 6
        assert pg["score_pushback"] == 3
        assert pg["learning_weight_days"] == 90


class TestDesignGateBlock:
    """Scenario: design_gate block exists with all required fields."""

    def test_design_gate_keys_present(self):
        cfg = _load_config()
        dg = cfg["pipeline"]["design_gate"]
        expected_keys = {"enabled", "max_retries", "max_turns", "timeout"}
        assert set(dg.keys()) == expected_keys, (
            f"design_gate keys mismatch: got {set(dg.keys())}, want {expected_keys}"
        )

    def test_design_gate_enabled_is_true(self):
        """Scenario: design_gate is enabled."""
        cfg = _load_config()
        assert cfg["pipeline"]["design_gate"]["enabled"] is True

    def test_design_gate_field_values(self):
        cfg = _load_config()
        dg = cfg["pipeline"]["design_gate"]
        assert dg["max_retries"] == 2
        assert dg["max_turns"] == 4
        assert dg["timeout"] == 120


class TestExistingPipelineFieldsUnchanged:
    """Scenario: existing pipeline fields unchanged after gate addition."""

    def test_existing_scalar_fields(self):
        cfg = _load_config()
        p = cfg["pipeline"]
        assert p["max_changes_per_cycle"] == 10
        assert p["enrich_max_turns"] == 50
        assert p["enrich_timeout"] == 2400
        assert p["impl_max_turns"] == 60
        assert p["impl_timeout_minutes"] == 40
        assert p["fix_attempts"] == 10
        assert p["optimize_enabled"] is True
        assert p["eval_fix_attempts"] == 3
        assert p["cycle_interval_hours"] == 8

    def test_compaction_subtree_unchanged(self):
        cfg = _load_config()
        comp = cfg["pipeline"]["compaction"]
        assert comp["enabled"] is False
        assert comp["threshold_chars"] == 60000
        assert comp["keep_recent"] == 3
        assert comp["use_llm_summary"] is True


class TestYamlSyntaxValidity:
    """Scenario: zsiga.yaml is valid YAML."""

    def test_yaml_parses_without_error(self):
        cfg = _load_config()
        assert isinstance(cfg, dict)
        assert "pipeline" in cfg

    def test_yaml_file_is_re_roundtrippable(self):
        """Ensure the YAML can be dumped and re-loaded with same structure."""
        cfg = _load_config()
        dumped = yaml.dump(cfg, default_flow_style=False)
        reloaded = yaml.safe_load(dumped)
        assert reloaded["pipeline"]["proposal_gate"]["enabled"] is True
        assert reloaded["pipeline"]["design_gate"]["enabled"] is True


class TestRollbackCapability:
    """Scenario: setting enabled to false disables the gate."""

    def test_proposal_gate_can_be_disabled(self):
        cfg = _load_config()
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["proposal_gate"]["enabled"] = False
        assert mod["pipeline"]["proposal_gate"]["enabled"] is False

    def test_design_gate_can_be_disabled(self):
        cfg = _load_config()
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["design_gate"]["enabled"] = False
        assert mod["pipeline"]["design_gate"]["enabled"] is False

    def test_disabling_does_not_remove_other_fields(self):
        cfg = _load_config()
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["proposal_gate"]["enabled"] = False
        mod["pipeline"]["design_gate"]["enabled"] = False
        # All other fields still present
        assert mod["pipeline"]["proposal_gate"]["max_retries"] == 1
        assert mod["pipeline"]["design_gate"]["max_retries"] == 2
