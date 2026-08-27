"""Tests for create-transport-factory spec — create_transport function."""
from unittest.mock import MagicMock

from zsiga.transport import create_transport, LocalTransport, SSHTransport


def test_create_transport_without_ssh_returns_local():
    """target_config without ssh returns LocalTransport."""
    cfg = MagicMock()
    cfg.ssh = None
    result = create_transport(cfg)
    assert isinstance(result, LocalTransport)


def test_create_transport_with_ssh_returns_ssh_transport():
    """target_config with ssh returns SSHTransport with correct params."""
    ssh = MagicMock()
    ssh.host = "srv"
    ssh.user = "bob"
    ssh.port = 2222
    ssh.key_path = "/home/bob/.ssh/id"

    cfg = MagicMock()
    cfg.ssh = ssh

    result = create_transport(cfg)
    assert isinstance(result, SSHTransport)
    assert result.host == "srv"
    assert result.user == "bob"
    assert result.port == 2222


def test_create_transport_with_minimal_ssh_uses_defaults():
    """target_config with ssh but minimal fields uses defaults."""
    ssh = MagicMock()
    ssh.host = "srv"
    ssh.user = None
    ssh.port = 22
    ssh.key_path = None

    cfg = MagicMock()
    cfg.ssh = ssh

    result = create_transport(cfg)
    assert isinstance(result, SSHTransport)
    assert result.port == 22
    assert result.key_path is None
