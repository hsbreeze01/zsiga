"""Change Conflict Detector — scan pending changes for file overlaps."""

import re
from dataclasses import dataclass, field

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

    # -- Convenience: build full dependency graph ---------------------------

    def build_graph(self, changes_dir: str) -> "DependencyGraph":
        """Scan changes and build a full dependency graph in one call."""
        changes = self.scan_changes(changes_dir)
        return build_dependency_graph(changes, transport=self._transport)


# ---------------------------------------------------------------------------
# Dependency Graph data models
# ---------------------------------------------------------------------------

@dataclass
class ConflictEdge:
    """A directed edge representing a conflict/dependency between two changes."""

    from_id: str
    to_id: str
    conflict_type: str          # "file_overlap" | "explicit_dep"
    severity: str               # "HIGH" | "LOW" | "NONE"
    shared_files: list[str]     # empty for explicit deps


@dataclass
class DependencyGraph:
    """DAG of change dependencies."""

    nodes: dict[str, ChangeInfo] = field(default_factory=dict)
    adjacency: dict[str, set[str]] = field(default_factory=dict)
    edges: list[ConflictEdge] = field(default_factory=list)

    # -- Cycle detection (DFS three-color) ---------------------------------

    def detect_cycles(self) -> None:
        """Raise ``ValueError`` if a cycle exists in the graph."""
        WHITE, GREY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self.nodes}

        def _dfs(node: str, path: list[str]) -> None:
            color[node] = GREY
            path.append(node)
            for neighbour in sorted(self.adjacency.get(node, set())):
                if color[neighbour] == GREY:
                    cycle_start = path.index(neighbour)
                    cycle = path[cycle_start:] + [neighbour]
                    raise ValueError(
                        f"Circular dependency detected: {' -> '.join(cycle)}"
                    )
                if color[neighbour] == WHITE:
                    _dfs(neighbour, path)
            path.pop()
            color[node] = BLACK

        for nid in sorted(self.nodes):
            if color[nid] == WHITE:
                _dfs(nid, [])

    # -- Topological sort (Kahn's algorithm) --------------------------------

    def topological_order(self) -> list[str]:
        """Return change IDs in a safe execution order.

        Tiebreak: fewer target files first, then lexicographic ID.
        """
        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}
        for nid, neighbours in self.adjacency.items():
            for nb in neighbours:
                if nb in in_degree:
                    in_degree[nb] += 1

        # Seed with nodes having in-degree 0
        available = sorted(
            [nid for nid, deg in in_degree.items() if deg == 0],
            key=lambda n: (len(self.nodes[n].target_files), n),
        )
        result: list[str] = []

        while available:
            node = available.pop(0)
            result.append(node)
            for nb in sorted(self.adjacency.get(node, set())):
                if nb in in_degree:
                    in_degree[nb] -= 1
                    if in_degree[nb] == 0:
                        # Re-sort available with new entry
                        available.append(nb)
                        available.sort(
                            key=lambda n: (len(self.nodes[n].target_files), n)
                        )
        return result

    # -- Human-readable conflict report -------------------------------------

    def conflict_report(self) -> str:
        """Produce a human-readable summary of all conflicts and execution order."""
        lines: list[str] = []

        if self.edges:
            lines.append("Conflicts detected:")
            for edge in self.edges:
                shared = ", ".join(edge.shared_files) if edge.shared_files else ""
                if edge.conflict_type == "file_overlap":
                    lines.append(
                        f"  {edge.from_id} <-> {edge.to_id}: "
                        f"{edge.severity} conflict on {shared}"
                    )
                else:
                    lines.append(
                        f"  {edge.from_id} -> {edge.to_id}: "
                        f"explicit dependency"
                    )
        else:
            lines.append("No conflicts detected.")

        order = self.topological_order()
        lines.append("")
        lines.append("Suggested execution order:")
        for idx, nid in enumerate(order, 1):
            lines.append(f"  {idx}. {nid}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers for dependency graph construction
# ---------------------------------------------------------------------------

_DEPENDS_ON_RE = re.compile(r"<!--\s*depends-on:\s*(.+?)\s*-->")


def _parse_depends_on(tasks_content: str) -> list[str]:
    """Parse ``<!-- depends-on: id1, id2 -->`` declarations from tasks.md."""
    deps: list[str] = []
    for match in _DEPENDS_ON_RE.finditer(tasks_content):
        for ident in match.group(1).split(","):
            ident = ident.strip()
            if ident:
                deps.append(ident)
    return deps


def _severity_for_shared(shared_files: list[str]) -> str:
    """Return severity based on file extensions of shared files."""
    for f in shared_files:
        if f.endswith(".py"):
            return "HIGH"
    for f in shared_files:
        if f.endswith(".md"):
            return "LOW"
    return "NONE"


def build_dependency_graph(
    changes: list[ChangeInfo],
    transport: Transport = None,
) -> DependencyGraph:
    """Build a DAG from *changes*, combining file overlaps and explicit deps.

    For each change the corresponding ``tasks.md`` is read (if present) to
    extract ``<!-- depends-on: ... -->`` declarations.
    """
    transport = transport or LocalTransport()

    nodes: dict[str, ChangeInfo] = {c.id: c for c in changes}
    adjacency: dict[str, set[str]] = {c.id: set() for c in changes}
    edges: list[ConflictEdge] = []

    # 1. Explicit dependencies from tasks.md
    explicit_deps: dict[str, list[str]] = {}
    for change in changes:
        tasks_path = f"{change.change_dir}/tasks.md"
        content = read_file(tasks_path, transport)
        if content is not None:
            explicit_deps[change.id] = _parse_depends_on(content)
        else:
            explicit_deps[change.id] = []

    # Add explicit-dependency edges
    for change_id, deps in explicit_deps.items():
        for dep_id in deps:
            if dep_id in nodes:
                adjacency[dep_id].add(change_id)
                edges.append(ConflictEdge(
                    from_id=dep_id,
                    to_id=change_id,
                    conflict_type="explicit_dep",
                    severity="NONE",
                    shared_files=[],
                ))

    # 2. File-overlap edges
    relevant = [c for c in changes if c.target_files]
    n = len(relevant)
    for i in range(n):
        for j in range(i + 1, n):
            shared = relevant[i].target_files & relevant[j].target_files
            if shared:
                shared_list = sorted(shared)
                severity = _severity_for_shared(shared_list)
                a, b = relevant[i], relevant[j]
                # Determine direction; respect existing explicit-dep edges
                a_to_b = b.id in adjacency.get(a.id, set())
                b_to_a = a.id in adjacency.get(b.id, set())
                if a_to_b:
                    from_id, to_id = a.id, b.id
                elif b_to_a:
                    from_id, to_id = b.id, a.id
                elif len(a.target_files) <= len(b.target_files):
                    from_id, to_id = a.id, b.id
                else:
                    from_id, to_id = b.id, a.id
                # Only add to adjacency if not already connected (avoids cycles)
                if to_id not in adjacency.get(from_id, set()):
                    adjacency[from_id].add(to_id)
                edges.append(ConflictEdge(
                    from_id=from_id,
                    to_id=to_id,
                    conflict_type="file_overlap",
                    severity=severity,
                    shared_files=shared_list,
                ))

    graph = DependencyGraph(
        nodes=nodes,
        adjacency=adjacency,
        edges=edges,
    )
    graph.detect_cycles()
    return graph
