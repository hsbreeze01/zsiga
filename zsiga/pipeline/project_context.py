import re

from ..transport import Transport, LocalTransport
from .utils import read_file, file_exists


MAX_CONTEXT_CHARS = 25000


def build_project_context(target_path: str, transport: Transport = None,
                          proposal: str = "") -> str:
    transport = transport or LocalTransport()
    sections = []

    sections.append(_scan_tree(target_path, transport))

    key_files = _find_key_files(target_path, transport)
    for fpath, label in key_files:
        content = read_file(fpath, transport)
        if content:
            sections.append(f"### {label} ({fpath})\n```\n{content}\n```")

    keywords = _extract_keywords(proposal)

    sections.append(_scan_routes(target_path, transport, keywords))
    sections.append(_scan_services(target_path, transport, keywords))
    sections.append(_scan_models(target_path, transport, keywords))
    sections.append(_scan_templates(target_path, transport, keywords))
    sections.append(_scan_db_schema(target_path, transport))

    combined = "\n\n".join(s for s in sections if s)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[:MAX_CONTEXT_CHARS] + "\n\n... (truncated)"
    return combined


def _extract_keywords(text: str) -> list[str]:
    if not text:
        return []
    stop = {"add", "the", "a", "an", "to", "for", "in", "on", "of", "and", "with",
            "from", "by", "is", "are", "was", "were", "be", "been", "being",
            "this", "that", "it", "its", "or", "not", "no", "but", "at", "as",
            "api", "new", "create", "update", "delete", "get", "set", "list", "all"}
    words = re.findall(r'[a-zA-Z_]{3,}', text.lower())
    return list(set(w for w in words if w not in stop))[:10]


def _scan_tree(target_path: str, transport: Transport) -> str:
    r = transport.run_shell(
        f"find '{target_path}' -type f \\( -name '*.py' -o -name '*.html' -o -name '*.js' -o -name '*.css' \\) "
        f"-not -path '*/venv/*' -not -path '*/__pycache__/*' "
        f"-not -path '*/.git/*' -not -path '*/node_modules/*' "
        f"-not -path '*/migrations/*' -not -path '*/static/*' "
        f"| sort | head -100",
        timeout=15,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return ""
    files = r["stdout"].strip().split("\n")
    rel_paths = []
    for f in files:
        if f.startswith(target_path):
            f = f[len(target_path):].lstrip("/")
        rel_paths.append(f)
    return "## Project File Tree\n" + "\n".join(rel_paths)


def _find_key_files(target_path: str, transport: Transport) -> list[tuple[str, str]]:
    candidates = [
        ("config.py", "Config"),
        ("settings.py", "Config"),
        ("app.py", "App Entry"),
        ("main.py", "App Entry"),
        ("manage.py", "Manage"),
        ("requirements.txt", "Dependencies"),
        ("pyproject.toml", "Project Config"),
        ("setup.py", "Setup"),
    ]
    found = []
    for name, label in candidates:
        for search_dir in ["", "src/", "app/"]:
            fpath = f"{target_path}/{search_dir}{name}"
            if file_exists(fpath, transport):
                found.append((fpath, label))
                break
    return found[:5]


def _scan_routes(target_path: str, transport: Transport,
                 keywords: list[str] = None) -> str:
    r = transport.run_shell(
        f"find '{target_path}' -path '*/routes/*.py' -o -path '*/views/*.py' -o -path '*/api/*.py' "
        f"| grep -v __pycache__ | grep -v venv | sort | head -20",
        timeout=10,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return ""
    route_files = r["stdout"].strip().split("\n")
    if keywords:
        route_files = _prioritize(route_files, keywords, top=5)
    else:
        route_files = route_files[:5]
    parts = ["## API Routes"]
    for rf in route_files:
        rel = rf.replace(f"{target_path}/", "") if rf.startswith(target_path) else rf
        content = read_file(rf, transport)
        if content:
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            parts.append(f"### {rel}\n```\n{content}\n```")
    return "\n\n".join(parts)


def _scan_services(target_path: str, transport: Transport,
                   keywords: list[str] = None) -> str:
    r = transport.run_shell(
        f"find '{target_path}' -path '*/services/*.py' -not -path '*/venv/*' -not -path '*/__pycache__/*' "
        f"| sort | head -20",
        timeout=10,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return ""
    svc_files = r["stdout"].strip().split("\n")
    if keywords:
        svc_files = _prioritize(svc_files, keywords, top=5)
    else:
        svc_files = svc_files[:5]
    parts = ["## Services"]
    for sf in svc_files:
        rel = sf.replace(f"{target_path}/", "") if sf.startswith(target_path) else sf
        content = read_file(sf, transport)
        if content:
            if len(content) > 4000:
                content = content[:4000] + "\n... (truncated)"
            parts.append(f"### {rel}\n```\n{content}\n```")
    return "\n\n".join(parts)


def _scan_models(target_path: str, transport: Transport,
                 keywords: list[str] = None) -> str:
    r = transport.run_shell(
        f"find '{target_path}' -path '*/models/*.py' -not -path '*/venv/*' -not -path '*/__pycache__/*' "
        f"| sort | head -20",
        timeout=10,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return ""
    model_files = r["stdout"].strip().split("\n")
    if keywords:
        model_files = _prioritize(model_files, keywords, top=5)
    else:
        model_files = model_files[:5]
    parts = ["## Models"]
    for mf in model_files:
        rel = mf.replace(f"{target_path}/", "") if mf.startswith(target_path) else mf
        content = read_file(mf, transport)
        if content:
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            parts.append(f"### {rel}\n```\n{content}\n```")
    return "\n\n".join(parts)


def _scan_db_schema(target_path: str, transport: Transport) -> str:
    """Detect MySQL DB config and prefetch table schemas."""
    db_info = _detect_db_config(target_path, transport)
    if not db_info:
        return ""

    host, port, user, password, database = db_info
    # Single query: get all table schemas + row counts in one round-trip
    r = transport.run_shell(
        f"mysql -u{user} -p{password} -h{host} -P{port} {database} -e '"
        "SELECT TABLE_NAME, TABLE_ROWS, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT "
        "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, ORDINAL_POSITION;' "
        "2>/dev/null",
        timeout=20,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return ""

    rows = r["stdout"].strip().split("\n")
    if len(rows) < 2:
        return ""

    # Parse into per-table sections
    tables = {}
    for line in rows[1:]:
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        tname, trows, cname, ctype, nullable, ckey, _ = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
        if tname not in tables:
            tables[tname] = {"rows": trows, "columns": []}
        tables[tname]["columns"].append(f"{cname} {ctype} {'NULL' if nullable == 'YES' else 'NOT NULL'}{(' ' + ckey) if ckey else ''}")

    parts = [f"## Database Schema ({database}, {len(tables)} tables)"]
    for tname, info in list(tables.items())[:20]:
        parts.append(f"### {tname} (~{info['rows']} rows)\n```\n" + "\n".join(info["columns"]) + "\n```")

    result = "\n\n".join(parts)
    if len(result) > 8000:
        result = result[:8000] + "\n\n... (truncated)"
    return result


def _detect_db_config(target_path: str, transport: Transport) -> tuple | None:
    """Detect MySQL connection info from project config files."""
    # Skip DB scan for zsiga itself (no DB, and grep on large local dirs can timeout)
    if "zsiga" in target_path and "d8q-" not in target_path:
        return None
    # Strategy: grep for common DB config patterns
    r = transport.run_shell(
        f"cd '{target_path}' && grep -rn --include='*.py' --include='*.yaml' --include='*.yml' --include='*.json' "
        f"-E '(mysql|pymysql|host.*3306|database.*stock|DB_HOST|DBConnection)' "
        f"-l 2>/dev/null | grep -v venv | grep -v __pycache__ | grep -v pipeline/project_context.py | head -5",
        timeout=10,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return None

    config_files = r["stdout"].strip().split("\n")
    for cf in config_files:
        content = read_file(cf, transport)
        if not content:
            continue

        # Try to extract connection params
        import re
        host_m = re.search(r"host['\"]?\s*[:=]\s*['\"]?([^'\"\s,}]+)", content)
        port_m = re.search(r"port['\"]?\s*[:=]\s*['\"]?(\d+)", content)
        user_m = re.search(r"user['\"]?\s*[:=]\s*['\"]?([^'\"\s,}]+)", content)
        pw_m = re.search(r"(?:password|passwd)['\"]?\s*[:=]\s*['\"]?([^'\"\s,}]+)", content)
        db_m = re.search(r"(?:database|db)['\"]?\s*[:=]\s*['\"]?([^'\"\s,}]+)", content)

        if host_m and db_m:
            return (
                host_m.group(1),
                int(port_m.group(1)) if port_m else 3306,
                user_m.group(1) if user_m else "root",
                pw_m.group(1) if pw_m else "",
                db_m.group(1),
            )

    return None


def _prioritize(files: list[str], keywords: list[str], top: int = 5) -> list[str]:
    scored = []
    for f in files:
        score = 0
        fname = f.lower()
        for kw in keywords:
            if kw in fname:
                score += 2
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top]]


def _scan_templates(target_path: str, transport: Transport,
                    keywords: list[str] = None) -> str:
    r = transport.run_shell(
        f"find '{target_path}' -type f \\( -name '*.html' -o -name '*.js' \\) "
        f"-not -path '*/venv/*' -not -path '*/__pycache__/*' -not -path '*/.git/*' "
        f"-not -path '*/node_modules/*' -not -path '*/static/*' "
        f"| sort | head -20",
        timeout=10,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return ""
    template_files = r["stdout"].strip().split("\n")
    if keywords:
        template_files = _prioritize(template_files, keywords, top=3)
    else:
        template_files = template_files[:3]
    parts = ["## Frontend Templates"]
    for tf in template_files:
        rel = tf.replace(f"{target_path}/", "") if tf.startswith(target_path) else tf
        content = read_file(tf, transport)
        if content:
            if len(content) > 4000:
                content = content[:4000] + "\n... (truncated)"
            parts.append(f"### {rel}\n```\n{content}\n```")
    return "\n\n".join(parts)


def prefetch_mechanical(target_path: str, test_cmd: str, lint_cmd: str,
                        since_sha: str = None,
                        transport: Transport = None) -> dict:
    from .utils import verify_mechanical
    transport = transport or LocalTransport()

    passed, errors = verify_mechanical(
        target_path, test_cmd, lint_cmd,
        since_sha=since_sha, transport=transport,
    )

    test_passed = True
    lint_passed = True
    test_output = ""
    lint_output = ""
    if not passed:
        for section in errors.split("\n"):
            if section.startswith("tests:"):
                test_passed = False
                test_output = errors[errors.index("tests:"):]
            elif section.startswith("lint:"):
                lint_passed = False
                lint_output = errors[errors.index("lint:"):]

    return {
        "test": {"passed": test_passed, "output": test_output[-2000:]},
        "lint": {"passed": lint_passed, "output": lint_output[-2000:]},
    }
