import logging

from ..transport import Transport, LocalTransport

logger = logging.getLogger(__name__)


def _find_file_ci(directory_listing: list[str], target_name: str) -> str | None:
    """Case-insensitive file lookup within a directory listing.

    Args:
        directory_listing: List of filenames (not paths) from ``os.listdir`` or similar.
        target_name: The canonical lowercase name, e.g. ``"proposal.md"``.

    Returns:
        The actual filename with its original casing, or ``None`` if not found.
    """
    target_lower = target_name.lower()
    for name in directory_listing:
        if name.lower() == target_lower:
            return name
    return None


class DirectoryScanner:

    def __init__(self, targets: dict):
        self.targets = targets

    def scan(self, transports: dict = None) -> list[dict]:
        transports = transports or {}
        proposals = []
        for project_name, target in self.targets.items():
            transport = transports.get(project_name, LocalTransport())
            changes_dir = f"{target.path}/openspec/changes"

            r = transport.run_shell(f"test -d '{changes_dir}' && echo EXISTS", timeout=10)
            if "EXISTS" not in r.get("stdout", ""):
                continue

            r = transport.run_shell(f"ls -1 '{changes_dir}'", timeout=10)
            if r["exit_code"] != 0:
                continue

            for entry_name in r["stdout"].strip().split("\n"):
                entry_name = entry_name.strip()
                if not entry_name or entry_name == "archive":
                    continue

                change_dir = f"{changes_dir}/{entry_name}"
                r = transport.run_shell(f"test -d '{change_dir}' && echo DIR", timeout=5)
                if "DIR" not in r.get("stdout", ""):
                    continue

                # List directory contents for case-insensitive file detection
                r = transport.run_shell(f"ls -1 '{change_dir}'", timeout=5)
                dir_listing = r["stdout"].strip().split("\n") if r["exit_code"] == 0 else []

                proposal_filename = _find_file_ci(dir_listing, "proposal.md")
                if proposal_filename is None:
                    logger.warning(
                        f"⚠ Scanner: directory {change_dir} exists but no proposal.md found (case-insensitive search)"
                    )
                    continue

                design_filename = _find_file_ci(dir_listing, "design.md")
                tasks_filename = _find_file_ci(dir_listing, "tasks.md")
                clarify_filename = _find_file_ci(dir_listing, "clarify.md")

                r_specs = transport.run_shell(
                    f"test -d '{change_dir}/specs' && echo YES", timeout=5
                )

                proposals.append({
                    "id": entry_name,
                    "project": project_name,
                    "target_path": target.path,
                    "change_dir": change_dir,
                    "has_proposal": True,
                    "has_specs": "YES" in r_specs.get("stdout", ""),
                    "has_design": design_filename is not None,
                    "has_tasks": tasks_filename is not None,
                    "has_clarify": clarify_filename is not None,
                    "proposal_filename": proposal_filename,
                    "design_filename": design_filename,
                    "tasks_filename": tasks_filename,
                    "clarify_filename": clarify_filename,
                })
        return proposals

    def is_enriched(self, proposal: dict) -> bool:
        # New format: specs/ + clarify.md
        if proposal["has_specs"] and proposal.get("has_clarify"):
            return True
        # Legacy format: specs/ + design.md + tasks.md
        return proposal["has_specs"] and proposal["has_design"] and proposal["has_tasks"]

    def is_fully_implemented(self, proposal: dict, transport: Transport = None) -> bool:
        transport = transport or LocalTransport()
        tasks_name = proposal.get("tasks_filename") or "tasks.md"
        tasks_file = f"{proposal['change_dir']}/{tasks_name}"
        r = transport.run_shell(f"cat '{tasks_file}'", timeout=10)
        if r["exit_code"] != 0:
            return False
        content = r["stdout"]
        unchecked = content.count("- [ ]")
        return unchecked == 0
