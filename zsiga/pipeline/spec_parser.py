"""Spec scenario parser for the P1-5 spec → pytest pipeline.

Parses an OpenSpec markdown spec and returns a list of :class:`Scenario`
objects, each with:

- ``name``: the scenario heading
- ``testable``: bool flag from ``- **testable**: true|false`` (default ``False``)
- ``target``: optional :class:`TargetRef` parsed from
  ``- **target**: <file>::<symbol>`` (default ``None``)
- ``given``/``when``/``then``: extracted from the
  ``- **Given/When/Then** ...`` bullet lines
- ``raw_block``: the original markdown block (heading + body) for
  Layer-2 LLM fallback so we never lose information

Format additions are introduced incrementally — old specs that lack the
``testable`` and ``target`` fields parse cleanly with sensible defaults
(``testable=False``, ``target=None``), so legacy proposals keep working.

Phase-1 scope (per ``feedback-to-kiro-spec-pytest-20260521`` Q1):
- ``<file>::<function>``         → ``TargetRef(file=..., symbol=...)``
- ``<file>::<Class>.<method>``   → ``TargetRef(file=..., symbol=Class.method)``
- ``cli:<command>`` and ``http:<...>`` are recognised but raise
  :class:`UnsupportedTargetKind` so callers can defer them to L2.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Target reference (extension point)
# ---------------------------------------------------------------------------


class UnsupportedTargetKind(ValueError):
    """Raised when a target string uses a kind we don't yet handle."""


@dataclass(frozen=True)
class TargetRef:
    """Reference to a thing under test.

    Phase 1 only fills ``file`` + ``symbol``. Future kinds (cli / http)
    will populate ``kind`` differently.
    """

    file: str
    symbol: str
    kind: str = "python"   # "python" | "cli" | "http" — only "python" today

    @property
    def is_method(self) -> bool:
        return "." in self.symbol


_PY_TARGET_RE = re.compile(
    r"^(?P<file>[\w./-]+\.py)"
    r"::"
    r"(?P<symbol>[A-Za-z_][\w.]*)"
    r"$"
)


def parse_target(raw: str) -> TargetRef:
    """Parse a ``target`` field value.

    Accepts ``<file>.py::<symbol>`` and ``<file>.py::<Class>.<method>``.
    Other recognised-but-unsupported prefixes raise
    :class:`UnsupportedTargetKind` so the caller can fall back gracefully.
    """
    s = raw.strip()
    if not s:
        raise ValueError("empty target")

    if s.startswith("cli:"):
        raise UnsupportedTargetKind(f"cli targets not supported in Phase 1: {s!r}")
    if s.startswith("http:"):
        raise UnsupportedTargetKind(f"http targets not supported in Phase 1: {s!r}")

    m = _PY_TARGET_RE.match(s)
    if not m:
        raise ValueError(
            f"target {s!r} does not match <file>.py::<symbol> "
            "(Phase 1 supports python targets only)"
        )
    return TargetRef(file=m.group("file"), symbol=m.group("symbol"), kind="python")


# ---------------------------------------------------------------------------
# Scenario model
# ---------------------------------------------------------------------------


@dataclass
class Scenario:
    name: str
    testable: bool = False
    target: TargetRef | None = None
    given: str = ""
    when: str = ""
    then: str = ""
    raw_block: str = ""
    target_error: str | None = None
    """If parsing the target string failed, the error text is captured here.

    The scenario stays parseable (testable=False forced) so the rest of
    the pipeline keeps running and the issue surfaces in REVIEW.
    """

    @property
    def slug(self) -> str:
        """Filename-friendly slug derived from ``name``."""
        # lowercase, alnum + '_' only, collapse runs of non-alnum
        s = re.sub(r"[^a-zA-Z0-9]+", "_", self.name).strip("_").lower()
        return s or "scenario"


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------

# Match scenario headings of any depth >= 3 (### / #### / #####).
_HEADING_RE = re.compile(
    r"^(?P<hashes>#{3,6})\s*Scenario\s*:\s*(?P<name>.+?)\s*$",
    re.MULTILINE,
)

# Match `- **field**: value` / `* **field**: value` / `**field**: value`
_BOLD_FIELD_RE = re.compile(
    r"^[\s*\-]*\*\*(?P<field>[A-Za-z_][\w-]*)\*\*\s*:?\s*(?P<value>.*?)\s*$",
    re.IGNORECASE,
)


def _split_scenario_blocks(spec_text: str) -> list[tuple[str, str]]:
    """Return a list of ``(heading_line, body_text)`` per Scenario block."""
    matches = list(_HEADING_RE.finditer(spec_text))
    if not matches:
        return []

    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        heading_line = m.group(0)
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(spec_text)
        body = spec_text[body_start:body_end].strip("\n")
        # When deciding the boundary we also stop at a higher-level heading
        # (one with fewer or equal '#' than the next scenario) to stay safe;
        # since _HEADING_RE only fires on Scenario headings this is moot.
        blocks.append((heading_line, body))
    return blocks


def _parse_bool(value: str) -> bool | None:
    v = value.strip().lower()
    if v in ("true", "yes", "1"):
        return True
    if v in ("false", "no", "0", ""):
        return False
    return None


def _parse_block(heading_line: str, body: str) -> Scenario:
    name_match = _HEADING_RE.match(heading_line)
    name = name_match.group("name").strip() if name_match else heading_line.strip()

    raw_block = f"{heading_line}\n{body}".rstrip() + "\n"
    sc = Scenario(name=name, raw_block=raw_block)

    for line in body.splitlines():
        m = _BOLD_FIELD_RE.match(line.rstrip())
        if not m:
            continue
        field_name = m.group("field").lower()
        value = m.group("value").strip()
        if field_name == "testable":
            parsed = _parse_bool(value)
            if parsed is not None:
                sc.testable = parsed
        elif field_name == "target":
            try:
                sc.target = parse_target(value)
            except (ValueError, UnsupportedTargetKind) as exc:
                sc.target = None
                sc.target_error = f"{exc.__class__.__name__}: {exc}"
                # Force testable=False so we don't try to build a pytest
                # for a scenario whose target we couldn't parse.
                sc.testable = False
        elif field_name == "given":
            sc.given = value
        elif field_name == "when":
            sc.when = value
        elif field_name == "then":
            sc.then = value

    return sc


def parse_spec(spec_text: str) -> list[Scenario]:
    """Parse all Scenario blocks from a single spec markdown.

    Empty / non-spec markdown returns an empty list. Malformed scenarios
    do not raise — fields they cannot fill stay at their defaults so the
    pipeline can still run REVIEW / VERIFY-L2 against the raw markdown.
    """
    blocks = _split_scenario_blocks(spec_text)
    return [_parse_block(h, b) for h, b in blocks]


def collect_testable(scenarios: list[Scenario]) -> list[Scenario]:
    """Convenience filter for callers that only want L1-eligible items."""
    return [s for s in scenarios if s.testable and s.target is not None]
