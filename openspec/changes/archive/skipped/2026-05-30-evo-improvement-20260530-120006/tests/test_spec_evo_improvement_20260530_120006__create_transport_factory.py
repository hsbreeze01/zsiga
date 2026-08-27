"""Spec tests for create_transport factory function.

Covers specs: create-transport-factory.md
"""
from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransport:
    """create_transport factory function."""

    def test_returns_local_transport_for_none_ssh(self):
        """Scenario: create_transport returns LocalTransport for None ssh."""
        config = SimpleNamespace(ssh=None)
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_returns_local_transport_when_ssh_attr_missing(self):
        """Scenario: create_transport returns LocalTransport when ssh attr missing."""
        config = SimpleNamespace()  # no ssh attribute
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_transport_with_ssh_config(self):
        """Scenario: create_transport returns SSHTransport with ssh config."""
        ssh = SimpleNamespace(host="myhost", user="alice", port=2222,
                              key_path="/key")
        config = SimpleNamespace(ssh=ssh)
        result = create_transport(config)
        assert isinstance(result, SSHTransport)
        assert result.host == "myhost"
        assert result.user == "alice"
        assert result.port == 2222
        assert result.key_path == "/key"
