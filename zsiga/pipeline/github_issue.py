"""GitHub Issue creation for proposal-commit linkage.

This module provides two public functions:
- ``create_issue(owner_repo, title, body, token)`` → ``int | None``
- ``extract_github_repo(target_path, transport)`` → ``str | None``

All errors are caught internally and logged as warnings. No function in this
module ever raises on GitHub API or git-remote failures.
"""

import json
import re
import subprocess

from ..transport import Transport


_SSH_PATTERN = re.compile(r"(?:git@|ssh://git@)[^:/]+[:/](.+?)(?:\.git)?$")
_HTTPS_PATTERN = re.compile(r"https?://github\.com/(.+?)(?:\.git)?$")


def extract_github_repo(target_path: str, transport: Transport) -> str | None:
    """Extract ``owner/repo`` from the target's ``git remote get-url origin``.

    Supports SSH (``git@github.com:owner/repo.git``) and HTTPS
    (``https://github.com/owner/repo.git``) formats. Returns ``None`` on any
    failure.
    """
    try:
        r = transport.run_shell(
            "git remote get-url origin", cwd=target_path, timeout=10,
        )
        if r["exit_code"] != 0:
            return None
        url = r["stdout"].strip()
    except Exception as exc:
        print(f"  [github] Failed to get remote URL: {exc}")
        return None

    # Try SSH pattern first (covers alias hosts like github-agent)
    m = _SSH_PATTERN.match(url)
    if m:
        return m.group(1)

    # Try HTTPS pattern
    m = _HTTPS_PATTERN.match(url)
    if m:
        return m.group(1)

    print(f"  [github] Cannot parse remote URL: {url}")
    return None


def create_issue(
    owner_repo: str,
    title: str,
    body: str,
    token: str,
) -> int | None:
    """Create a GitHub Issue via the REST API (curl).

    Returns the issue number on success, or ``None`` on any failure.
    """
    if not token:
        print("  [github] No token provided, skipping Issue creation")
        return None

    url = f"https://api.github.com/repos/{owner_repo}/issues"
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": ["zsiga"],
    })
    # Escape single quotes in payload for shell safety
    payload_escaped = payload.replace("'", "'\\''")

    cmd = (
        f"curl -s -w '\\n%{{http_code}}' -X POST "
        f"-H 'Authorization: token {token}' "
        f"-H 'Accept: application/vnd.github.v3+json' "
        f"-d '{payload_escaped}' "
        f"'{url}'"
    )

    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        print("  [github] curl timed out creating Issue")
        return None
    except Exception as exc:
        print(f"  [github] curl failed: {exc}")
        return None

    # curl output: response body + status code on last line
    output = r.stdout
    parts = output.rsplit("\n", 1)
    if len(parts) < 2:
        print(f"  [github] Unexpected curl output: {output[:200]}")
        return None

    body_text, status_str = parts[0], parts[1].strip()
    try:
        status_code = int(status_str)
    except ValueError:
        print(f"  [github] Cannot parse HTTP status from: {status_str}")
        return None

    if status_code < 200 or status_code >= 300:
        print(
            f"  [github] Issue creation failed (HTTP {status_code}): "
            f"{body_text[:200]}"
        )
        return None

    try:
        data = json.loads(body_text)
        issue_number = data.get("number")
        if issue_number is not None:
            print(f"  [github] Created Issue #{issue_number}")
            return int(issue_number)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"  [github] Failed to parse Issue response: {exc}")

    return None
