import subprocess
from pathlib import Path


class DirectoryScanner:

    def __init__(self, targets: dict):
        self.targets = targets

    def scan(self) -> list[dict]:
        proposals = []
        for project_name, target in self.targets.items():
            changes_dir = Path(target.path) / "openspec" / "changes"
            if not changes_dir.exists():
                continue
            for change_dir in sorted(changes_dir.iterdir()):
                if not change_dir.is_dir():
                    continue
                if change_dir.name == "archive":
                    continue
                proposal_file = change_dir / "proposal.md"
                if not proposal_file.exists():
                    continue
                proposals.append({
                    "id": change_dir.name,
                    "project": project_name,
                    "target_path": target.path,
                    "change_dir": str(change_dir),
                    "has_proposal": True,
                    "has_specs": (change_dir / "specs").exists(),
                    "has_design": (change_dir / "design.md").exists(),
                    "has_tasks": (change_dir / "tasks.md").exists(),
                })
        return proposals

    def is_enriched(self, proposal: dict) -> bool:
        return proposal["has_specs"] and proposal["has_design"] and proposal["has_tasks"]

    def is_fully_implemented(self, proposal: dict) -> bool:
        tasks_file = Path(proposal["change_dir"]) / "tasks.md"
        if not tasks_file.exists():
            return False
        content = tasks_file.read_text()
        unchecked = content.count("- [ ]")
        return unchecked == 0
