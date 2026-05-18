"""Skill Evolution: cluster mined patterns into skills and generate markdown files."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from zsiga.memory.pattern_miner import Pattern, Severity, mine_patterns


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ClusterInfo:
    """Aggregated information for a group of related patterns."""

    prefix: str  # e.g. "pipeline.fail"
    patterns: list[Pattern] = field(default_factory=list)
    total_count: int = 0
    all_takeaways: list[str] = field(default_factory=list)
    severity: Severity = "low"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cluster_prefix(pattern_key: str) -> str:
    """Return the cluster prefix: first two dot-delimited segments (or first one)."""
    parts = pattern_key.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return parts[0]


def _cluster_patterns(patterns: list[Pattern]) -> dict[str, ClusterInfo]:
    """Group Pattern objects by shared dot-prefix and aggregate stats."""
    clusters: dict[str, ClusterInfo] = {}

    for pat in patterns:
        prefix = _cluster_prefix(pat.key)
        if prefix not in clusters:
            clusters[prefix] = ClusterInfo(prefix=prefix)
        cluster = clusters[prefix]
        cluster.patterns.append(pat)
        cluster.total_count += pat.count
        cluster.all_takeaways.extend(pat.recent_takeaways)
        # highest severity wins
        sev_order = {"high": 3, "medium": 2, "low": 1}
        if sev_order.get(pat.severity, 0) > sev_order.get(cluster.severity, 0):
            cluster.severity = pat.severity

    # deduplicate takeaways while preserving order
    for cluster in clusters.values():
        seen: set[str] = set()
        deduped: list[str] = []
        for tw in cluster.all_takeaways:
            if tw not in seen:
                seen.add(tw)
                deduped.append(tw)
        cluster.all_takeaways = deduped

    return clusters


def _derive_filename(prefix: str) -> str:
    """Convert a cluster prefix to a skill filename.

    Example: ``pipeline.fail`` → ``pipeline-fail.md``
    """
    return prefix.replace(".", "-") + ".md"


def _generate_skill_markdown(cluster: ClusterInfo) -> str:
    """Produce full markdown content (frontmatter + body) for *cluster*."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    frontmatter = {
        "name": cluster.prefix.replace(".", " ").title(),
        "description": f"Auto-generated skill from {cluster.total_count} recurring patterns",
        "auto_generated": True,
    }

    lines: list[str] = []
    lines.append("---")
    lines.append(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {cluster.prefix.replace('.', ' ').title()}")
    lines.append("")
    lines.append(
        "> Auto-generated from recurring patterns in learnings.jsonl."
        f"\n> Last updated: {now}"
    )
    lines.append("")
    lines.append("## Patterns Observed")
    lines.append("")
    lines.append("| Pattern | Count | Severity |")
    lines.append("|---------|-------|----------|")
    for pat in sorted(cluster.patterns, key=lambda p: p.count, reverse=True):
        lines.append(f"| {pat.key} | {pat.count} | {pat.severity} |")
    lines.append("")
    lines.append("## Guidelines")
    lines.append("")
    for tw in cluster.all_takeaways:
        lines.append(f"- {tw}")
    lines.append("")

    return "\n".join(lines)


def _is_auto_generated(path: Path) -> bool:
    """Return True if the skill file at *path* has ``auto_generated: true``."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return False
    return bool(meta.get("auto_generated", False))


def _prune_stale_skills(
    skills_dir: Path,
    qualifying_prefixes: set[str],
) -> list[str]:
    """Delete auto-generated skill files whose cluster no longer qualifies.

    Returns list of deleted file paths (as strings).
    """
    deleted: list[str] = []
    if not skills_dir.exists():
        return deleted
    for md_file in skills_dir.glob("*.md"):
        if not _is_auto_generated(md_file):
            continue
        # Derive the expected prefix from the filename
        stem = md_file.stem  # e.g. "pipeline-fail"
        expected_prefix = stem.replace("-", ".")
        if expected_prefix not in qualifying_prefixes:
            md_file.unlink()
            deleted.append(str(md_file))
    return deleted


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evolve_skills(
    min_cluster_occurrences: int = 3,
    learnings_path: Optional[Path] = None,
    skills_dir: Optional[Path] = None,
) -> list[str]:
    """Full skill evolution pipeline: mine → cluster → generate → prune.

    Returns a list of generated/updated skill file paths.
    """
    skills_root = skills_dir or Path(__file__).resolve().parent

    # 1. Mine patterns
    patterns = mine_patterns(
        min_occurrences=1,  # get everything; threshold applied at cluster level
        learnings_path=learnings_path,
    )

    # 2. Cluster
    clusters = _cluster_patterns(patterns)

    # 3. Generate / update qualifying skill files
    written: list[str] = []
    qualifying_prefixes: set[str] = set()

    for prefix, cluster in clusters.items():
        if cluster.total_count < min_cluster_occurrences:
            continue
        qualifying_prefixes.add(prefix)

        skills_root.mkdir(parents=True, exist_ok=True)
        filename = _derive_filename(prefix)
        filepath = skills_root / filename

        # Skip hand-written files
        if filepath.exists() and not _is_auto_generated(filepath):
            continue

        content = _generate_skill_markdown(cluster)
        filepath.write_text(content, encoding="utf-8")
        written.append(str(filepath))

    # 4. Prune stale auto-generated skills
    _prune_stale_skills(skills_root, qualifying_prefixes)

    return written
