"""Tests for spec: create-transport-factory

Covers create_transport factory function returning LocalTransport or SSHTransport.
"""
from types import SimpleNamespace
from zsiga.transport import create_transport, LocalTransport, SSHTransport


# ---------------------------------------------------------------------------
# create_transport returns LocalTransport without ssh config
# ---------------------------------------------------------------------------
def test_create_transport_returns_local_without_ssh():
    """create_transport returns LocalTransport when target_config has no ssh."""
    config = SimpleNamespace()
    result = create_transport(config)
    assert isinstance(result, LocalTransport)


# ---------------------------------------------------------------------------
# create_transport returns LocalTransport when ssh is None
# ---------------------------------------------------------------------------
def test_create_transport_returns_local_when_ssh_none():
    """create_transport returns LocalTransport when target_config.ssh is None."""
    config = SimpleNamespace(ssh=None)
    result = create_transport(config)
    assert isinstance(result, LocalTransport)


# ---------------------------------------------------------------------------
# create_transport returns SSHTransport with ssh config
# ---------------------------------------------------------------------------
def test_create_transport_returns_ssh_with_config():
    """create_transport returns SSHTransport when target_config.ssh is truthy."""
    ssh_cfg = SimpleNamespace(host="myhost", user="admin", port=2222, key_path="/key")
    config = SimpleNamespace(ssh=ssh_cfg)
    result = create_transport(config)
    assert isinstance(result, SSHTransport)
    assert result.host == "myhost"
    assert result.user == "admin"
    assert result.port == 2222
    assert result.key_path == "/key"
