"""Proposal Deduplication Checker — detect duplicate proposals against archive."""

import re
from dataclasses import dataclass

from ..transport import Transport, LocalTransport
from .utils import read_file


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ArchivedProposal:
    id: str                     # archived change directory name
    proposal_text: str          # raw proposal.md content


@dataclass
class DuplicateMatch:
    change_id: str              # archived change directory name
    score: float                # similarity score [0.0, 1.0]
    proposal_text: str          # the matched archived proposal text (for context)


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(r"^#\s*Proposal\s*:\s*", re.MULTILINE)


def normalize(text: str) -> str:
    """Normalize proposal text for comparison.

    - Lowercase
    - Strip ``# Proposal:`` header prefix
    - Remove non-alphanumeric characters except spaces
    - Collapse whitespace
    """
    text = _HEADER_RE.sub("", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute Jaccard similarity on word sets of normalized texts.

    Returns a float between 0.0 (completely dissimilar) and 1.0 (identical).
    """
    words_a = set(normalize(text_a).split())
    words_b = set(normalize(text_b).split())
    union = words_a | words_b
    if not union:
        return 1.0
    intersection = words_a & words_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Load archived proposals
# ---------------------------------------------------------------------------

def load_archived_proposals(archive_dir: str,
                            transport: Transport = None) -> list[ArchivedProposal]:
    """Load all proposal texts from archived openspec changes.

    Scans subdirectories of *archive_dir*, reads each ``proposal.md``,
    and returns a list of :class:`ArchivedProposal` entries.  Subdirectories
    without a ``proposal.md`` are silently skipped.
    """
    transport = transport or LocalTransport()
    r = transport.run_shell(
        f"find '{archive_dir}' -mindepth 1 -maxdepth 1 -type d | sort",
        timeout=10,
    )
    if r["exit_code"] != 0:
        return []

    results: list[ArchivedProposal] = []
    for line in r["stdout"].strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        dirname = line.rsplit("/", 1)[-1]
        proposal_path = f"{line}/proposal.md"
        content = read_file(proposal_path, transport)
        if content is not None:
            results.append(ArchivedProposal(
                id=dirname,
                proposal_text=content,
            ))
    return results


# ---------------------------------------------------------------------------
# Check duplicates
# ---------------------------------------------------------------------------

def check_duplicates(new_text: str, archive_dir: str,
                     threshold: float = 0.5,
                     transport: Transport = None) -> list[DuplicateMatch]:
    """Compare *new_text* against all archived proposals.

    Returns a list of :class:`DuplicateMatch` entries whose score is
    at or above *threshold*, sorted by score descending.
    """
    archived = load_archived_proposals(archive_dir, transport)
    matches: list[DuplicateMatch] = []
    for ap in archived:
        score = compute_similarity(new_text, ap.proposal_text)
        if score >= threshold:
            matches.append(DuplicateMatch(
                change_id=ap.id,
                score=score,
                proposal_text=ap.proposal_text,
            ))
    matches.sort(key=lambda m: m.score, reverse=True)
    return matches
