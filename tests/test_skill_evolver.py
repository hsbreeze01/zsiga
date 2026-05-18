"""Tests for skills/skill_evolver.py"""

import json
from pathlib import Path

import yaml

from skills.skill_evolver import (
    ClusterInfo,
    _cluster_patterns,
    _derive_filename,
    _generate_skill_markdown,
    _is_auto_generated,
    evolve_skills,
)
from zsiga.memory.pattern_miner import Pattern


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_learnings(path: Path, records: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# 1. Clustering
# ---------------------------------------------------------------------------

class TestClusterPatterns:

    def test_cluster_pipeline_failure_patterns(self):
        """Scenario: Cluster pipeline failure patterns."""
        patterns = [
            Pattern(key="pipeline.fail.implement", count=6, severity="high",
                    recent_takeaways=["check imports"]),
            Pattern(key="pipeline.fail.verify", count=2, severity="high",
                    recent_takeaways=["run tests"]),
            Pattern(key="pipeline.fail.escalation", count=1, severity="high",
                    recent_takeaways=["ask for help"]),
        ]
        clusters = _cluster_patterns(patterns)
        assert "pipeline.fail" in clusters
        cluster = clusters["pipeline.fail"]
        assert len(cluster.patterns) == 3
        assert cluster.total_count == 9
        assert cluster.severity == "high"

    def test_cluster_single_segment_key(self):
        """Scenario: Cluster single-segment keys (first segment only)."""
        patterns = [
            Pattern(key="ops.service_management", count=3, severity="medium",
                    recent_takeaways=["use systemctl"]),
        ]
        clusters = _cluster_patterns(patterns)
        # first two segments → "ops.service_management"
        assert "ops.service_management" in clusters
        assert clusters["ops.service_management"].total_count == 3

    def test_cluster_two_segment_key(self):
        """Key with exactly two segments stays as-is."""
        patterns = [
            Pattern(key="tools.venv_detection", count=4, severity="medium",
                    recent_takeaways=["use venv"]),
        ]
        clusters = _cluster_patterns(patterns)
        assert "tools.venv_detection" in clusters

    def test_cluster_deduplicates_takeaways(self):
        patterns = [
            Pattern(key="pipeline.fail.test", count=3, severity="high",
                    recent_takeaways=["check imports", "check imports", "run tests"]),
        ]
        clusters = _cluster_patterns(patterns)
        cluster = clusters["pipeline.fail"]
        assert cluster.all_takeaways == ["check imports", "run tests"]

    def test_cluster_highest_severity(self):
        patterns = [
            Pattern(key="pipeline.fail.test", count=5, severity="low",
                    recent_takeaways=[]),
            Pattern(key="pipeline.fail.implement", count=3, severity="high",
                    recent_takeaways=[]),
        ]
        clusters = _cluster_patterns(patterns)
        assert clusters["pipeline.fail"].severity == "high"

    def test_cluster_empty(self):
        assert _cluster_patterns([]) == {}


# ---------------------------------------------------------------------------
# 2. Skill file generation
# ---------------------------------------------------------------------------

class TestGenerateSkillMarkdown:

    def test_generates_yaml_frontmatter(self):
        cluster = ClusterInfo(
            prefix="pipeline.fail",
            patterns=[
                Pattern(key="pipeline.fail.implement", count=6, severity="high",
                        recent_takeaways=["check imports"]),
                Pattern(key="pipeline.fail.verify", count=2, severity="high",
                        recent_takeaways=["run tests"]),
            ],
            total_count=8,
            all_takeaways=["check imports", "run tests"],
            severity="high",
        )
        md = _generate_skill_markdown(cluster)
        assert md.startswith("---")
        # Parse frontmatter
        parts = md.split("---", 2)
        meta = yaml.safe_load(parts[1])
        assert meta["auto_generated"] is True
        assert "pipeline.fail" in meta["description"].lower() or "8" in meta["description"]

    def test_includes_pattern_table(self):
        cluster = ClusterInfo(
            prefix="pipeline.fail",
            patterns=[
                Pattern(key="pipeline.fail.implement", count=6, severity="high",
                        recent_takeaways=[]),
            ],
            total_count=6,
            all_takeaways=["check imports"],
            severity="high",
        )
        md = _generate_skill_markdown(cluster)
        assert "pipeline.fail.implement" in md
        assert "| 6 |" in md
        assert "high" in md

    def test_includes_guidelines(self):
        cluster = ClusterInfo(
            prefix="tools.venv_detection",
            patterns=[
                Pattern(key="tools.venv_detection", count=3, severity="medium",
                        recent_takeaways=["use venv path"]),
            ],
            total_count=3,
            all_takeaways=["use venv path"],
            severity="medium",
        )
        md = _generate_skill_markdown(cluster)
        assert "## Guidelines" in md
        assert "- use venv path" in md


# ---------------------------------------------------------------------------
# 3. Filename derivation
# ---------------------------------------------------------------------------

class TestDeriveFilename:

    def test_dot_to_hyphen(self):
        assert _derive_filename("pipeline.fail") == "pipeline-fail.md"

    def test_single_segment(self):
        assert _derive_filename("ops") == "ops.md"

    def test_multi_segment(self):
        assert _derive_filename("tools.venv_detection") == "tools-venv_detection.md"


# ---------------------------------------------------------------------------
# 4. Auto-generated detection
# ---------------------------------------------------------------------------

class TestIsAutoGenerated:

    def test_detects_auto_generated(self, tmp_path):
        skill = tmp_path / "auto.md"
        skill.write_text("---\nauto_generated: true\nname: test\n---\n\nBody\n")
        assert _is_auto_generated(skill) is True

    def test_detects_hand_written(self, tmp_path):
        skill = tmp_path / "hand.md"
        skill.write_text("---\nname: test\ndescription: manual\n---\n\nBody\n")
        assert _is_auto_generated(skill) is False

    def test_nonexistent_file(self, tmp_path):
        assert _is_auto_generated(tmp_path / "nope.md") is False

    def test_no_frontmatter(self, tmp_path):
        skill = tmp_path / "plain.md"
        skill.write_text("Just plain text\n")
        assert _is_auto_generated(skill) is False


# ---------------------------------------------------------------------------
# 5. Full evolution pipeline
# ---------------------------------------------------------------------------

class TestEvolveSkills:

    def test_full_pipeline_generates_skills(self, tmp_path):
        """Scenario: Full evolution pipeline."""
        learnings = tmp_path / "learnings.jsonl"
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "check imports", "ts": "2026-01-01"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "verify setup", "ts": "2026-01-02"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "check types", "ts": "2026-01-03"},
            {"pattern_key": "pipeline.fail.verify", "takeaway": "run tests", "ts": "2026-01-04"},
            {"pattern_key": "pipeline.fail.verify", "takeaway": "check coverage", "ts": "2026-01-05"},
            {"pattern_key": "pipeline.fail.verify", "takeaway": "fix lint", "ts": "2026-01-06"},
        ])

        skills_dir = tmp_path / "skills"
        result = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert len(result) == 1
        assert "pipeline-fail.md" in result[0]
        # Verify file content
        content = (skills_dir / "pipeline-fail.md").read_text()
        meta = yaml.safe_load(content.split("---")[1])
        assert meta["auto_generated"] is True

    def test_empty_learnings(self, tmp_path):
        """Scenario: No qualifying clusters returns empty list."""
        learnings = tmp_path / "learnings.jsonl"
        learnings.write_text("")
        skills_dir = tmp_path / "skills"
        result = evolve_skills(learnings_path=learnings, skills_dir=skills_dir)
        assert result == []

    def test_below_threshold_no_files(self, tmp_path):
        """Scenario: Skip cluster below threshold."""
        learnings = tmp_path / "learnings.jsonl"
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.test", "takeaway": "a"},
            {"pattern_key": "pipeline.fail.test", "takeaway": "b"},
            # only 2 occurrences of pipeline.fail.test → cluster total = 2 < 3
        ])
        skills_dir = tmp_path / "skills"
        result = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert result == []
        assert list(skills_dir.glob("*.md")) == []

    def test_idempotent_regenerates(self, tmp_path):
        """Scenario: Update existing auto-generated skill."""
        learnings = tmp_path / "learnings.jsonl"
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "a"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "b"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "c"},
        ])
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # First generation
        result1 = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert len(result1) == 1
        content1 = (skills_dir / "pipeline-fail.md").read_text()

        # Add more data
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "a"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "d"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "e"},
        ] + json.loads("[" + learnings.read_text().strip().replace("\n", ",") + "]"))

        # Actually, let's just write all records properly
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "a"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "b"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "c"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "d"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "e"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "f"},
        ])

        # Re-generate
        result2 = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert len(result2) == 1
        content2 = (skills_dir / "pipeline-fail.md").read_text()
        # Updated content should differ
        assert content1 != content2

    def test_preserves_hand_written(self, tmp_path):
        """Scenario: Preserve hand-written skills."""
        learnings = tmp_path / "learnings.jsonl"
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "a"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "b"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "c"},
        ])
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # Hand-written skill file
        hand_written = skills_dir / "pipeline-fail.md"
        hand_written.write_text("---\nname: implement\ndescription: manual\n---\n\nManual content\n")

        result = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert result == []
        # File unchanged
        assert hand_written.read_text() == "---\nname: implement\ndescription: manual\n---\n\nManual content\n"

    def test_prune_stale_skill(self, tmp_path):
        """Scenario: Remove stale skill file."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # Auto-generated skill that will become stale
        stale = skills_dir / "pipeline-fail.md"
        stale.write_text("---\nauto_generated: true\nname: test\n---\n\nOld content\n")

        # Learnings with no pipeline.fail patterns
        learnings = tmp_path / "learnings.jsonl"
        learnings.write_text("")

        result = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert result == []
        assert not stale.exists()

    def test_multiple_clusters(self, tmp_path):
        """Test that multiple qualifying clusters produce multiple files."""
        learnings = tmp_path / "learnings.jsonl"
        _write_learnings(learnings, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "a"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "b"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "c"},
            {"pattern_key": "ops.restart", "takeaway": "use systemctl"},
            {"pattern_key": "ops.restart", "takeaway": "use systemctl"},
            {"pattern_key": "ops.restart", "takeaway": "use systemctl"},
        ])
        skills_dir = tmp_path / "skills"
        result = evolve_skills(
            min_cluster_occurrences=3,
            learnings_path=learnings,
            skills_dir=skills_dir,
        )
        assert len(result) == 2
        filenames = [Path(p).name for p in result]
        assert "pipeline-fail.md" in filenames
        assert "ops-restart.md" in filenames
