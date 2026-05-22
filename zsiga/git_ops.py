from .transport import Transport, LocalTransport


def _check_result(result: dict, operation_label: str):
    """Check git operation result; raise RuntimeError on failure."""
    if result["exit_code"] != 0:
        stderr = result.get("stderr", "").strip()
        print(f"  ❌ {operation_label} failed: {stderr}")
        raise RuntimeError(stderr)


def rev_parse(target_path: str, transport: Transport = None) -> str:
    transport = transport or LocalTransport()
    r = transport.run_shell("git rev-parse HEAD", cwd=target_path)
    return r["stdout"].strip()


def reset_hard(target_path: str, sha: str, transport: Transport = None):
    transport = transport or LocalTransport()
    print(f"  git reset --hard {sha} ...")
    r = transport.run_shell(f"git reset --hard {sha}", cwd=target_path)
    _check_result(r, "git reset")
    r2 = transport.run_shell("git clean -fd", cwd=target_path)
    _check_result(r2, "git clean")
    print("  ✅ reset hard")


def add_all(target_path: str, transport: Transport = None):
    transport = transport or LocalTransport()
    print("  git add -A ...")
    r = transport.run_shell("git add -A", cwd=target_path)
    _check_result(r, "git add")
    print("  ✅ added all")


def commit(target_path: str, message: str, transport: Transport = None):
    transport = transport or LocalTransport()
    print(f"  git commit -m '{message}' ...")
    r = transport.run_shell(f"git commit -m '{message}'", cwd=target_path)
    _check_result(r, "git commit")
    print("  ✅ committed")


def tag(target_path: str, tag_name: str, transport: Transport = None, force: bool = False):
    transport = transport or LocalTransport()
    print(f"  git tag -a {tag_name} ...")
    if force:
        transport.run_shell(f"git tag -d {tag_name} || true", cwd=target_path)
    r = transport.run_shell(f"git tag -a {tag_name} -m .zsiga: {tag_name}.", cwd=target_path)
    _check_result(r, "git tag")
    print(f"  ✅ tagged {tag_name}")


def push(target_path: str, remote: str = "origin", branch: str | None = None,
         dry_run: bool = False, transport: Transport = None):
    transport = transport or LocalTransport()
    if branch is None:
        branch = current_branch(target_path, transport=transport)
    if dry_run:
        print(f"  [DRY RUN] git push {remote} {branch} --tags")
        return
    print(f"  git push {remote} {branch} ...")
    r = transport.run_shell(f"git push {remote} {branch}", cwd=target_path)
    _check_result(r, "git push")
    r2 = transport.run_shell("git push --tags", cwd=target_path)
    _check_result(r2, "git push --tags")
    print(f"  ✅ pushed {remote} {branch}")


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
    print(f"  git checkout -b {branch_name} ...")
    r = transport.run_shell(f"git checkout -b {branch_name}", cwd=target_path)
    _check_result(r, "git checkout -b")
    print(f"  ✅ created branch {branch_name}")


def checkout(target_path: str, ref: str, transport: Transport = None):
    transport = transport or LocalTransport()
    print(f"  git checkout {ref} ...")
    r = transport.run_shell(f"git checkout {ref}", cwd=target_path)
    _check_result(r, "git checkout")
    print(f"  ✅ checked out {ref}")


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
    print(f"  git merge {source} ...")
    r = transport.run_shell(f"git merge {source}", cwd=target_path)
    _check_result(r, "git merge")
    print(f"  ✅ merged {source}")


def delete_branch(target_path: str, branch_name: str, transport: Transport = None):
    transport = transport or LocalTransport()
    print(f"  git branch -D {branch_name} ...")
    r = transport.run_shell(f"git branch -D {branch_name}", cwd=target_path)
    _check_result(r, "git branch -D")
    print(f"  ✅ deleted branch {branch_name}")


def pull(target_path: str, remote: str = "origin", branch: str | None = None,
         transport: Transport = None):
    transport = transport or LocalTransport()
    if branch is None:
        branch = current_branch(target_path, transport=transport)
    print(f"  git pull {remote} {branch} ...")
    r = transport.run_shell(f"git pull {remote} {branch}", cwd=target_path)
    _check_result(r, "git pull")
    print(f"  ✅ pulled {remote} {branch}")
