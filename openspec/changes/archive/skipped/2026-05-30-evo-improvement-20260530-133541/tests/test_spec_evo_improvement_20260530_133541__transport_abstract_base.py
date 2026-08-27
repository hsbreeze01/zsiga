"""Tests for transport-abstract-base spec — Transport base class behaviour."""
from zsiga.transport import Transport


def test_transport_run_shell_raises_not_implemented():
    """Transport.run_shell raises NotImplementedError on direct call."""
    t = Transport()
    try:
        t.run_shell("echo hi")
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass


def test_transport_close_returns_none():
    """Transport.close returns None by default."""
    t = Transport()
    result = t.close()
    assert result is None


def test_subclass_without_run_shell_raises_not_implemented():
    """Subclass of Transport that does not override run_shell raises NotImplementedError."""
    class IncompleteTransport(Transport):
        pass

    t = IncompleteTransport()
    try:
        t.run_shell("ls")
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass
