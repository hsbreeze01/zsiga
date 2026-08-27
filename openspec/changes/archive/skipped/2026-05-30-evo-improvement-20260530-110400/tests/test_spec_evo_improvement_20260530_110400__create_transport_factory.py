"""Tests for create-transport-factory spec.

Covers create_transport factory function.
"""
from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransport:
    def test_no_ssh_attribute_returns_local(self):
        """Scenario: create_transport with no ssh attribute returns LocalTransport"""
        config = SimpleNamespace()
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_ssh_none_returns_local(self):
        """Scenario: create_transport with ssh=None returns LocalTransport"""
        config = SimpleNamespace(ssh=None)
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_ssh_config_returns_ssh_transport(self):
        """Scenario: create_transport with ssh config returns SSHTransport"""
        ssh = SimpleNamespace(host="myhost", user="alice", port=2222,
                              key_path="/home/alice/.ssh/id_rsa")
        config = SimpleNamespace(ssh=ssh)
        result = create_transport(config)
        assert isinstance(result, SSHTransport)
        assert result.host == "myhost"
        assert result.user == "alice"
        assert result.port == 2222
        assert result.key_path == "/home/alice/.ssh/id_rsa"
