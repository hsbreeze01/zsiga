import subprocess
from pathlib import Path


def rev_parse(target_path: str) -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=target_path, capture_output=True, text=True,
    )
    return r.stdout.strip()


def reset_hard(target_path: str, sha: str):
    subprocess.run(["git", "reset", "--hard", sha], cwd=target_path, check=True)
    subprocess.run(["git", "clean", "-fd"], cwd=target_path, capture_output=True)


def add_all(target_path: str):
    subprocess.run(["git", "add", "-A"], cwd=target_path, check=True)


def commit(target_path: str, message: str):
    subprocess.run(["git", "commit", "-m", message], cwd=target_path, check=True)


def tag(target_path: str, tag_name: str):
    subprocess.run(
        ["git", "tag", "-a", tag_name, "-m", f"zsiga: {tag_name}"],
        cwd=target_path, check=True,
    )


def push(target_path: str, remote: str = "origin", branch: str = "main",
         dry_run: bool = False):
    if dry_run:
        print(f"  [DRY RUN] git push {remote} {branch} --tags")
        return
    subprocess.run(
        ["git", "push", remote, branch],
        cwd=target_path, check=True,
    )
    subprocess.run(["git", "push", "--tags"], cwd=target_path, check=True)


def diff(target_path: str, since_sha: str) -> str:
    r = subprocess.run(
        ["git", "diff", since_sha, "HEAD"],
        cwd=target_path, capture_output=True, text=True,
    )
    return r.stdout


def has_uncommitted_changes(target_path: str) -> bool:
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target_path, capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def create_branch(target_path: str, branch_name: str):
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=target_path, check=True,
    )


def checkout(target_path: str, ref: str):
    subprocess.run(["git", "checkout", ref], cwd=target_path, check=True)
