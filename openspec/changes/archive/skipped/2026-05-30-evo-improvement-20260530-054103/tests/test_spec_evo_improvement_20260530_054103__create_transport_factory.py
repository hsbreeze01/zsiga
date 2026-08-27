"""Tests for spec: create-transport-factory.md
Change: evo-improvement-20260530-054103
"""

from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransport:
    """create_transport factory function scenarios."""

    def test_returns_local_transport_when_no_ssh(self):
        """Scenario: returns LocalTransport for config without ssh."""
        config = SimpleNamespace()
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_returns_local_transport_when_ssh_is_none(self):
        """Scenario: returns LocalTransport when ssh attribute is None."""
        config = SimpleNamespace(ssh=None)
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_transport_when_ssh_present(self):
        """Scenario: returns SSHTransport for config with ssh."""
        ssh = SimpleNamespace(host="srv", user="alice", port=2222, key_path="/key")
        config = SimpleNamespace(ssh=ssh)
        result = create_transport(config)

        assert isinstance(result, SSHTransport)
        assert result.host == "srv"
        assert result.user == "alice"
        assert result.port == 2222
        assert result.key_path == "/key"
