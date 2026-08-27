"""Tests for create-transport-factory.md spec scenarios.

Covers: create_transport factory function
"""
from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransport:
    """Spec: create_transport returns correct transport based on config."""

    def test_returns_local_transport_without_ssh(self):
        """Scenario: create_transport returns LocalTransport without ssh config."""
        cfg = SimpleNamespace(ssh=None)
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_local_transport_when_no_ssh_attribute(self):
        """Scenario: create_transport returns LocalTransport when no ssh attr."""
        cfg = SimpleNamespace()
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_transport_with_ssh_config(self):
        """Scenario: create_transport returns SSHTransport with ssh config."""
        ssh_cfg = SimpleNamespace(host="srv", user="u", port=2222, key_path="/key")
        cfg = SimpleNamespace(ssh=ssh_cfg)
        result = create_transport(cfg)
        assert isinstance(result, SSHTransport)
        assert result.host == "srv"
        assert result.user == "u"
        assert result.port == 2222
        assert result.key_path == "/key"
