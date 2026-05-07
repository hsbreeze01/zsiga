from ..transport import Transport, LocalTransport


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

                r = transport.run_shell(
                    f"test -f '{change_dir}/proposal.md' && echo YES", timeout=5
                )
                if "YES" not in r.get("stdout", ""):
                    continue

                r_specs = transport.run_shell(
                    f"test -d '{change_dir}/specs' && echo YES", timeout=5
                )
                r_design = transport.run_shell(
                    f"test -f '{change_dir}/design.md' && echo YES", timeout=5
                )
                r_tasks = transport.run_shell(
                    f"test -f '{change_dir}/tasks.md' && echo YES", timeout=5
                )

                proposals.append({
                    "id": entry_name,
                    "project": project_name,
                    "target_path": target.path,
                    "change_dir": change_dir,
                    "has_proposal": True,
                    "has_specs": "YES" in r_specs.get("stdout", ""),
                    "has_design": "YES" in r_design.get("stdout", ""),
                    "has_tasks": "YES" in r_tasks.get("stdout", ""),
                })
        return proposals

    def is_enriched(self, proposal: dict) -> bool:
        return proposal["has_specs"] and proposal["has_design"] and proposal["has_tasks"]

    def is_fully_implemented(self, proposal: dict, transport: Transport = None) -> bool:
        transport = transport or LocalTransport()
        tasks_file = f"{proposal['change_dir']}/tasks.md"
        r = transport.run_shell(f"cat '{tasks_file}'", timeout=10)
        if r["exit_code"] != 0:
            return False
        content = r["stdout"]
        unchecked = content.count("- [ ]")
        return unchecked == 0
