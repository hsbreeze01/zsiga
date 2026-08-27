"""Tests for zsiga/transport.py — create_transport factory spec tests."""
from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransportFactory:
    def test_returns_local_when_ssh_none(self):
        cfg = SimpleNamespace(ssh=None)
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_local_when_no_ssh_attribute(self):
        cfg = SimpleNamespace()
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_when_ssh_config_present(self):
        ssh_cfg = SimpleNamespace(host="myhost", user="ubuntu", port=2222, key_path="/key")
        cfg = SimpleNamespace(ssh=ssh_cfg)
        result = create_transport(cfg)
        assert isinstance(result, SSHTransport)
        assert result.host == "myhost"
        assert result.user == "ubuntu"
        assert result.port == 2222
        assert result.key_path == "/key"
