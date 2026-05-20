from .transport import Transport, LocalTransport


def rev_parse(target_path: str, transport: Transport = None) -> str:
    transport = transport or LocalTransport()
    r = transport.run_shell("git rev-parse HEAD", cwd=target_path)
    return r["stdout"].strip()


def reset_hard(target_path: str, sha: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git reset --hard {sha}", cwd=target_path)
    transport.run_shell("git clean -fd", cwd=target_path)


def add_all(target_path: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell("git add -A", cwd=target_path)


def commit(target_path: str, message: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git commit -m '{message}'", cwd=target_path)


def tag(target_path: str, tag_name: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git tag -a {tag_name} -m 'zsiga: {tag_name}'", cwd=target_path)


def push(target_path: str, remote: str = "origin", branch: str = "main",
         dry_run: bool = False, transport: Transport = None):
    transport = transport or LocalTransport()
    if dry_run:
        print(f"  [DRY RUN] git push {remote} {branch} --tags")
        return
    transport.run_shell(f"git push {remote} {branch}", cwd=target_path)
    transport.run_shell("git push --tags", cwd=target_path)


def diff(target_path: str, since_sha: str, transport: Transport = None) -> str:
    transport = transport or LocalTransport()
    r = transport.run_shell(f"git diff {since_sha} HEAD", cwd=target_path)
    return r["stdout"]


def has_uncommitted_changes(target_path: str, transport: Transport = None) -> bool:
    transport = transport or LocalTransport()
    r = transport.run_shell("git status --porcelain", cwd=target_path)
    return bool(r["stdout"].strip())


def create_branch(target_path: str, branch_name: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git checkout -b {branch_name}", cwd=target_path)


def checkout(target_path: str, ref: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git checkout {ref}", cwd=target_path)


def branch_exists(target_path: str, branch_name: str, transport: Transport = None) -> bool:
    transport = transport or LocalTransport()
    r = transport.run_shell(
        f"git rev-parse --verify {branch_name}", cwd=target_path
    )
    return r["exit_code"] == 0


def current_branch(target_path: str, transport: Transport = None) -> str:
    transport = transport or LocalTransport()
    r = transport.run_shell(
        "git rev-parse --abbrev-ref HEAD", cwd=target_path
    )
    return r["stdout"].strip()


def merge_branch(target_path: str, source: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git merge {source}", cwd=target_path)


def delete_branch(target_path: str, branch_name: str, transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git branch -D {branch_name}", cwd=target_path)


def pull(target_path: str, remote: str = "origin", branch: str = "main",
         transport: Transport = None):
    transport = transport or LocalTransport()
    transport.run_shell(f"git pull {remote} {branch}", cwd=target_path)
