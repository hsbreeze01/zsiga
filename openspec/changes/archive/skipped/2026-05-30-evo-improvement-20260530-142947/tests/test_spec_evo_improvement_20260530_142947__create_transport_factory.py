"""Spec tests for create-transport-factory.

Change: evo-improvement-20260530-142947
Spec:   create-transport-factory
"""

from unittest.mock import MagicMock

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransportFactorySpec:
    def test_returns_ssh_transport_for_ssh_target(self):
        cfg = MagicMock()
        cfg.ssh = MagicMock()
        cfg.ssh.host = "h"
        cfg.ssh.user = "u"
        cfg.ssh.port = 22
        cfg.ssh.key_path = "/key"
        result = create_transport(cfg)
        assert isinstance(result, SSHTransport)
        assert result.host == "h"
        assert result.user == "u"
        assert result.port == 22
        assert result.key_path == "/key"

    def test_returns_local_transport_when_ssh_is_none(self):
        cfg = MagicMock()
        cfg.ssh = None
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_local_transport_when_ssh_is_falsy(self):
        cfg = MagicMock()
        cfg.ssh = False
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)
