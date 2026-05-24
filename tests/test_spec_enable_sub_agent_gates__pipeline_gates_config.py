"""Tests for pipeline-gates-config spec (enable-sub-agent-gates change).

Verifies that zsiga.yaml contains proposal_gate and design_gate configuration
blocks with correct fields and values, while preserving existing config.
Also verifies that zsiga/config.py correctly parses these blocks into
PipelineConfig attributes.
Covers all testable scenarios from:
  - pipeline-gates-config.md
"""
import copy
import re
from collections import Counter
from pathlib import Path

import yaml


YAML_PATH = Path(__file__).resolve().parent.parent / "zsiga.yaml"


def _load_config():
    """Load and return the zsiga.yaml config dict."""
    assert YAML_PATH.exists(), f"zsiga.yaml not found at {YAML_PATH}"
    with open(YAML_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Proposal Gate Configuration Block
# ---------------------------------------------------------------------------


class TestProposalGateBlockStructure:
    """Scenario: proposal-gate-block-structure"""

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

    def test_proposal_gate_field_values(self):
        cfg = _load_config()
        pg = cfg["pipeline"]["proposal_gate"]
        assert pg["max_retries"] == 1
        assert pg["steward_max_turns"] == 3
        assert pg["steward_timeout"] == 90
        assert pg["score_accept"] == 6
        assert pg["score_pushback"] == 3
        assert pg["learning_weight_days"] == 90


class TestProposalGateEnabledTrue:
    """Scenario: proposal-gate-enabled-true"""

    def test_enabled_is_true_bool(self):
        cfg = _load_config()
        val = cfg["pipeline"]["proposal_gate"]["enabled"]
        assert val is True, f"Expected True (bool), got {val!r} (type={type(val).__name__})"


class TestProposalGateValueTypes:
    """Scenario: proposal-gate-value-types"""

    def test_enabled_is_bool(self):
        cfg = _load_config()
        assert isinstance(cfg["pipeline"]["proposal_gate"]["enabled"], bool)

    def test_numeric_fields_are_int(self):
        cfg = _load_config()
        pg = cfg["pipeline"]["proposal_gate"]
        int_fields = [
            "max_retries",
            "steward_max_turns",
            "steward_timeout",
            "score_accept",
            "score_pushback",
            "learning_weight_days",
        ]
        for field in int_fields:
            assert isinstance(pg[field], int), (
                f"proposal_gate.{field} is {type(pg[field]).__name__}, expected int"
            )


# ---------------------------------------------------------------------------
# Design Gate Configuration Block
# ---------------------------------------------------------------------------


class TestDesignGateBlockStructure:
    """Scenario: design-gate-block-structure"""

    def test_design_gate_keys_present(self):
        cfg = _load_config()
        dg = cfg["pipeline"]["design_gate"]
        expected_keys = {"enabled", "max_retries", "max_turns", "timeout"}
        assert set(dg.keys()) == expected_keys, (
            f"design_gate keys mismatch: got {set(dg.keys())}, want {expected_keys}"
        )

    def test_design_gate_field_values(self):
        cfg = _load_config()
        dg = cfg["pipeline"]["design_gate"]
        assert dg["max_retries"] == 2
        assert dg["max_turns"] == 4
        assert dg["timeout"] == 120


class TestDesignGateEnabledTrue:
    """Scenario: design-gate-enabled-true"""

    def test_enabled_is_true_bool(self):
        cfg = _load_config()
        val = cfg["pipeline"]["design_gate"]["enabled"]
        assert val is True, f"Expected True (bool), got {val!r} (type={type(val).__name__})"


class TestDesignGateValueTypes:
    """Scenario: design-gate-value-types"""

    def test_enabled_is_bool(self):
        cfg = _load_config()
        assert isinstance(cfg["pipeline"]["design_gate"]["enabled"], bool)

    def test_numeric_fields_are_int(self):
        cfg = _load_config()
        dg = cfg["pipeline"]["design_gate"]
        int_fields = ["max_retries", "max_turns", "timeout"]
        for field in int_fields:
            assert isinstance(dg[field], int), (
                f"design_gate.{field} is {type(dg[field]).__name__}, expected int"
            )


# ---------------------------------------------------------------------------
# Config Parsing Integration
# ---------------------------------------------------------------------------


class TestConfigParsesProposalGate:
    """Scenario: config-parses-proposal-gate"""

    def test_proposal_gate_enabled(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_enabled is True, (
            f"Expected proposal_gate_enabled=True, got {config.pipeline.proposal_gate_enabled!r}"
        )

    def test_proposal_gate_max_retries(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_max_retries == 1

    def test_proposal_gate_steward_max_turns(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_steward_max_turns == 3

    def test_proposal_gate_steward_timeout(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_steward_timeout == 90

    def test_proposal_gate_score_accept(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_score_accept == 6

    def test_proposal_gate_score_pushback(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_score_pushback == 3

    def test_proposal_gate_learning_weight_days(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.proposal_gate_learning_weight_days == 90


class TestConfigParsesDesignGate:
    """Scenario: config-parses-design-gate"""

    def test_design_gate_enabled(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.design_gate_enabled is True, (
            f"Expected design_gate_enabled=True, got {config.pipeline.design_gate_enabled!r}"
        )

    def test_design_gate_max_retries(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.design_gate_max_retries == 2

    def test_design_gate_max_turns(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.design_gate_max_turns == 4

    def test_design_gate_timeout(self):
        from zsiga.config import load_config

        config = load_config(str(YAML_PATH))
        assert config.pipeline.design_gate_timeout == 120


# ---------------------------------------------------------------------------
# Existing Pipeline Config Preservation
# ---------------------------------------------------------------------------


class TestExistingPipelineScalarsUnchanged:
    """Scenario: existing-pipeline-scalars-unchanged"""

    def test_scalar_fields(self):
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


class TestCompactionSubtreeUnchanged:
    """Scenario: compaction-subtree-unchanged"""

    def test_compaction_values(self):
        cfg = _load_config()
        comp = cfg["pipeline"]["compaction"]
        assert comp["enabled"] is False
        assert comp["threshold_chars"] == 60000
        assert comp["keep_recent"] == 3
        assert comp["use_llm_summary"] is True


# ---------------------------------------------------------------------------
# YAML Syntax Validity
# ---------------------------------------------------------------------------


class TestYamlSafeLoadSucceeds:
    """Scenario: yaml-safe-load-succeeds"""

    def test_loads_without_error(self):
        cfg = _load_config()
        assert isinstance(cfg, dict)
        assert "pipeline" in cfg


class TestYamlRoundtripPreservesGates:
    """Scenario: yaml-roundtrip-preserves-gates"""

    def test_roundtrip_proposal_gate(self):
        cfg = _load_config()
        dumped = yaml.dump(cfg, default_flow_style=False)
        reloaded = yaml.safe_load(dumped)
        assert reloaded["pipeline"]["proposal_gate"]["enabled"] is True

    def test_roundtrip_design_gate(self):
        cfg = _load_config()
        dumped = yaml.dump(cfg, default_flow_style=False)
        reloaded = yaml.safe_load(dumped)
        assert reloaded["pipeline"]["design_gate"]["enabled"] is True


class TestNoDuplicateYamlKeys:
    """Scenario: no-duplicate-yaml-keys"""

    def test_no_duplicate_keys_in_any_block(self):
        """Parse raw YAML text to detect duplicate keys within mapping blocks.

        yaml.safe_load silently uses the last value for duplicate keys,
        so we check the raw text instead.
        """
        text = YAML_PATH.read_text()
        lines = text.splitlines()

        # Track keys per indentation-level block
        # Simple heuristic: group consecutive non-blank, non-comment lines
        # by their indent level and check for duplicate key names
        current_indent = None
        keys_at_level = []

        for line in lines:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(stripped)
            # Extract key (before ':')
            key_match = re.match(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)", line)
            if not key_match:
                continue

            key = key_match.group(2)

            if indent != current_indent:
                # New block level — check previous block
                if keys_at_level:
                    counts = Counter(keys_at_level)
                    dups = {k: v for k, v in counts.items() if v > 1}
                    assert not dups, (
                        f"Duplicate keys at indent {current_indent}: {dups}"
                    )
                current_indent = indent
                keys_at_level = [key]
            else:
                keys_at_level.append(key)

        # Check last block
        if keys_at_level:
            counts = Counter(keys_at_level)
            dups = {k: v for k, v in counts.items() if v > 1}
            assert not dups, f"Duplicate keys at indent {current_indent}: {dups}"


# ---------------------------------------------------------------------------
# Rollback Capability
# ---------------------------------------------------------------------------


class TestProposalGateCanBeDisabled:
    """Scenario: proposal-gate-can-be-disabled"""

    def test_disable_proposal_gate_in_copy(self):
        cfg = _load_config()
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["proposal_gate"]["enabled"] = False
        assert mod["pipeline"]["proposal_gate"]["enabled"] is False
        # Other fields unchanged
        assert mod["pipeline"]["proposal_gate"]["max_retries"] == 1
        assert mod["pipeline"]["proposal_gate"]["steward_max_turns"] == 3

    def test_original_unchanged(self):
        cfg = _load_config()
        original_enabled = cfg["pipeline"]["proposal_gate"]["enabled"]
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["proposal_gate"]["enabled"] = False
        assert cfg["pipeline"]["proposal_gate"]["enabled"] == original_enabled


class TestDesignGateCanBeDisabled:
    """Scenario: design-gate-can-be-disabled"""

    def test_disable_design_gate_in_copy(self):
        cfg = _load_config()
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["design_gate"]["enabled"] = False
        assert mod["pipeline"]["design_gate"]["enabled"] is False
        # Other fields unchanged
        assert mod["pipeline"]["design_gate"]["max_retries"] == 2
        assert mod["pipeline"]["design_gate"]["max_turns"] == 4

    def test_original_unchanged(self):
        cfg = _load_config()
        original_enabled = cfg["pipeline"]["design_gate"]["enabled"]
        mod = copy.deepcopy(cfg)
        mod["pipeline"]["design_gate"]["enabled"] = False
        assert cfg["pipeline"]["design_gate"]["enabled"] == original_enabled
