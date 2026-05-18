"""Change Conflict Detector — scan pending changes for file overlaps."""

import re
from dataclasses import dataclass

from ..transport import Transport, LocalTransport
from .utils import read_file


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ChangeInfo:
    id: str                           # change directory name
    target_files: set[str]            # file paths parsed from design.md
    change_dir: str                   # full path to change directory


@dataclass
class ConflictPair:
    change_ids: tuple[str, str]       # sorted pair of change IDs
    shared_files: list[str]           # files targeted by both changes


# ---------------------------------------------------------------------------
# Regex for extracting target files from design.md
# ---------------------------------------------------------------------------

_FILE_RE = re.compile(r"`([^`]+\.(?:py|md))`")


def _extract_target_files(design_content: str) -> set[str]:
    """Parse design.md content for backtick-quoted file paths."""
    return set(_FILE_RE.findall(design_content))


# ---------------------------------------------------------------------------
# ChangeConflictDetector
# ---------------------------------------------------------------------------

class ChangeConflictDetector:
    """Detect file-level conflicts across pending openspec changes."""

    def __init__(self, transport: Transport = None):
        self._transport = transport or LocalTransport()

    # -- CCD-01: Scan Pending Changes --------------------------------------

    def scan_changes(self, changes_dir: str) -> list[ChangeInfo]:
        """List change subdirectories and parse each design.md.

        Subdirectories named ``archive`` are skipped.
        Changes without a ``design.md`` are still included with an empty
        ``target_files`` set.
        """
        r = self._transport.run_shell(
            f"find '{changes_dir}' -mindepth 1 -maxdepth 1 -type d | sort",
            timeout=10,
        )
        if r["exit_code"] != 0:
            return []

        results: list[ChangeInfo] = []
        for line in r["stdout"].strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Skip archive directory
            dirname = line.rsplit("/", 1)[-1]
            if dirname == "archive":
                continue
            # Read design.md
            design_path = f"{line}/design.md"
            content = read_file(design_path, self._transport)
            if content is not None:
                target_files = _extract_target_files(content)
            else:
                target_files = set()
            results.append(ChangeInfo(
                id=dirname,
                target_files=target_files,
                change_dir=line,
            ))
        return results

    # -- CCD-02: Find File Overlaps ----------------------------------------

    def find_overlaps(self, changes: list[ChangeInfo]) -> list[ConflictPair]:
        """Identify pairs of changes that share target files.

        Changes with empty ``target_files`` never appear in any conflict pair.
        """
        # Filter out changes with no target files
        relevant = [c for c in changes if c.target_files]
        pairs: list[ConflictPair] = []
        n = len(relevant)
        for i in range(n):
            for j in range(i + 1, n):
                shared = relevant[i].target_files & relevant[j].target_files
                if shared:
                    ids = tuple(sorted([relevant[i].id, relevant[j].id]))
                    pairs.append(ConflictPair(
                        change_ids=ids,
                        shared_files=sorted(shared),
                    ))
        return pairs

    # -- CCD-03: Suggest Execution Order -----------------------------------

    def suggest_order(self, changes: list[ChangeInfo]) -> list[str]:
        """Return change IDs ordered by recommended execution priority.

        Changes with fewer overlap edges come first.
        Tiebreaker: lexicographic change id.
        """
        # Build overlap count per change
        overlaps = self.find_overlaps(changes)
        overlap_count: dict[str, int] = {}
        for cp in overlaps:
            overlap_count[cp.change_ids[0]] = overlap_count.get(cp.change_ids[0], 0) + 1
            overlap_count[cp.change_ids[1]] = overlap_count.get(cp.change_ids[1], 0) + 1

        # Sort: fewer overlaps first, then fewer target files, then lexicographic id
        sorted_changes = sorted(
            changes,
            key=lambda c: (overlap_count.get(c.id, 0), len(c.target_files), c.id),
        )
        return [c.id for c in sorted_changes]
