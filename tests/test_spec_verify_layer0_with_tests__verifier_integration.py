"""Spec tests for verifier-layer0-integration.md.

Covers verify() Layer 0 early-return and Layer 1 continuation paths.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zsiga.pipeline.verify_layer0 import Layer0Check, Layer0Result, Transport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeTransport(Transport):
    """Minimal transport that records write calls."""

    def __init__(self):
        self.write_cmds: list[str] = []

    def run_shell(self, cmd, **kwargs):
        if cmd.startswith("cat > "):
            self.write_cmds.append(cmd)
        return {"exit_code": 0, "stdout": "", "stderr": ""}


def _make_result(passed: bool) -> Layer0Result:
    return Layer0Result(
        checks=[
            Layer0Check(
                id="fake",
                description="fake check",
                passed=passed,
                evidence="test evidence",
            )
        ]
    )


# ===================== Scenario tests =====================


@pytest.mark.asyncio
async def test_verify_returns_none_on_layer0_fail():
    """verify() returns None and writes FAIL verify.md when Layer 0 fails."""
    from zsiga.pipeline.verifier import verify

    fail_result = _make_result(passed=False)
    fake_agent = MagicMock()
    fake_transport = FakeTransport()

    with (
        patch("zsiga.pipeline.verifier.run_layer0_checks", return_value=fail_result),
        patch("zsiga.pipeline.verifier.write_layer0_verify_md") as mock_write,
        patch("zsiga.pipeline.verifier.LocalTransport", return_value=fake_transport),
    ):
        result = await verify(
            agent=fake_agent,
            change_dir="/tmp/change",
            target_path="/tmp/target",
            pre_impl_sha="abc123",
        )

    assert result is None
    mock_write.assert_called_once()


@pytest.mark.asyncio
async def test_verify_proceeds_to_layer1_on_layer0_pass():
    """verify() does NOT call write_layer0_verify_md when Layer 0 passes."""
    from zsiga.pipeline.verifier import verify

    pass_result = _make_result(passed=True)
    fake_agent = MagicMock()
    fake_agent.run = AsyncMock(return_value="LLM done")
    fake_transport = FakeTransport()

    # Layer 1 mock — non-vacuous, no non-testable scenarios → pure L1 fast path
    mock_layer1 = MagicMock()
    mock_layer1.vacuous = False
    mock_layer1.summary_line.return_value = "L1 PASS"
    mock_layer1.checks = []

    with (
        patch("zsiga.pipeline.verifier.run_layer0_checks", return_value=pass_result),
        patch("zsiga.pipeline.verifier.write_layer0_verify_md") as mock_write_l0,
        patch("zsiga.pipeline.verifier.run_layer1_pytest", return_value=mock_layer1),
        patch("zsiga.pipeline.verifier.has_non_testable_scenarios", return_value=False),
        patch("zsiga.pipeline.verifier.LocalTransport", return_value=fake_transport),
        patch("zsiga.pipeline.verifier._write_pure_layer1_verify_md"),
    ):
        result = await verify(
            agent=fake_agent,
            change_dir="/tmp/change",
            target_path="/tmp/target",
            pre_impl_sha="abc123",
        )

    mock_write_l0.assert_not_called()
