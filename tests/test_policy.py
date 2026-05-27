from zsiga.agent.permissions import (
    PermissionConfig,
    PermissionLevel,
    ensure_permissions,
    load_permissions,
)
from zsiga.agent.policy import check_bash_command, check_write_allowed
from zsiga.agent.tools import _edit_file, _write_file
from zsiga.transport import LocalTransport


def test_check_write_allowed_blocks_protected_path():
    decision = check_write_allowed("config/.env", ["**/.env"])
    assert decision.allowed is False
    assert "protected path" in decision.reason


def test_check_write_allowed_permits_regular_path():
    decision = check_write_allowed("src/app.py", ["**/.env"])
    assert decision.allowed is True


def test_write_file_returns_policy_error_for_protected_path(tmp_path):
    result = _write_file(
        LocalTransport(),
        str(tmp_path),
        ".env",
        "TOKEN=abc",
        protected_paths=["**/.env"],
    )
    assert result["error"].startswith("POLICY_DENIED")
    assert not (tmp_path / ".env").exists()


def test_edit_file_returns_policy_error_for_protected_path(tmp_path):
    target = tmp_path / "settings.py"
    target.write_text("x = 1\n")
    result = _edit_file(
        LocalTransport(),
        str(tmp_path),
        "settings.py",
        "x = 1",
        "x = 2",
        protected_paths=["settings.py"],
    )
    assert result["error"].startswith("POLICY_DENIED")
    assert target.read_text() == "x = 1\n"


def test_standard_permission_blocks_systemctl():
    decision = check_bash_command(
        "systemctl restart zsiga-daemon",
        permissions=PermissionConfig(level=PermissionLevel.STANDARD),
    )
    assert decision.allowed is False
    assert "advanced" in decision.reason


def test_standard_permission_allows_pytest():
    decision = check_bash_command(
        "venv/bin/python -m pytest -q tests/test_policy.py",
        permissions=PermissionConfig(level=PermissionLevel.STANDARD),
    )
    assert decision.allowed is True


def test_strict_permission_blocks_bash():
    decision = check_bash_command(
        "pytest -q",
        permissions=PermissionConfig(level=PermissionLevel.STRICT),
    )
    assert decision.allowed is False
    assert "strict" in decision.reason


def test_ensure_permissions_persists_standard_non_interactive(tmp_path):
    config = ensure_permissions(base_path=tmp_path, interactive=False)
    assert config.level is PermissionLevel.STANDARD
    assert (tmp_path / "data" / "permissions.json").exists()
    loaded = load_permissions(base_path=tmp_path)
    assert loaded.level is PermissionLevel.STANDARD
