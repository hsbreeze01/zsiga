"""
Spec tests for create_transport factory function.
Change: evo-improvement-20260530-065541
Spec: create-transport-factory
"""
from types import SimpleNamespace

from zsiga.transport import LocalTransport, SSHTransport, create_transport


class TestCreateTransportFactory:

    def test_returns_local_transport_for_no_ssh(self):
        """Scenario: create_transport returns LocalTransport for local config"""
        config = SimpleNamespace()
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_returns_local_transport_when_ssh_is_none(self):
        """Scenario: create_transport returns LocalTransport when ssh is None"""
        config = SimpleNamespace(ssh=None)
        result = create_transport(config)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_transport_for_ssh_config(self):
        """Scenario: create_transport returns SSHTransport for ssh config"""
        ssh = SimpleNamespace(host="myhost", user="ubuntu", port=2222, key_path="/key")
        config = SimpleNamespace(ssh=ssh)
        result = create_transport(config)

        assert isinstance(result, SSHTransport)
        assert result.host == "myhost"
        assert result.user == "ubuntu"
        assert result.port == 2222
        assert result.key_path == "/key"
