"""Tests for zsiga/transport.py — create_transport factory function."""
from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransportFactory:
    """create_transport returns correct Transport subclass."""

    def test_ssh_none_returns_local(self):
        """ssh=None → LocalTransport."""
        cfg = SimpleNamespace(ssh=None)
        assert isinstance(create_transport(cfg), LocalTransport)

    def test_no_ssh_attr_returns_local(self):
        """Missing ssh attribute → LocalTransport."""
        assert isinstance(create_transport(SimpleNamespace()), LocalTransport)

    def test_ssh_configured_returns_ssh_transport(self):
        """ssh config present → SSHTransport with forwarded params."""
        ssh = SimpleNamespace(host="h1", user="u1", port=2222, key_path="/k")
        cfg = SimpleNamespace(ssh=ssh)
        t = create_transport(cfg)
        assert isinstance(t, SSHTransport)
        assert t.host == "h1"
        assert t.user == "u1"
        assert t.port == 2222
        assert t.key_path == "/k"

    def test_ssh_empty_object_returns_local(self):
        """ssh is falsy (empty SimpleNamespace is truthy, but ssh=False) → LocalTransport."""
        cfg = SimpleNamespace(ssh=False)
        assert isinstance(create_transport(cfg), LocalTransport)
