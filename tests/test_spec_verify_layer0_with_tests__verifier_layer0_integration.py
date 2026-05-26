"""Spec tests for verifier-layer0-integration.md — verify() Layer 0 short-circuit."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from zsiga.pipeline.verify_layer0 import Layer0Check, Layer0Result


@pytest.mark.asyncio
async def test_verify_returns_none_on_layer0_fail():
    """Layer 0 FAIL → verify() returns None, does not invoke Layer 1."""
    fail_check = Layer0Check(
        id="spec_file_coverage", description="fail", passed=False, evidence="uncovered"
    )
    layer0_result = Layer0Result(checks=[fail_check], elapsed_seconds=0.01)

    mock_transport = MagicMock()
    mock_agent = MagicMock()

    with patch(
        "zsiga.pipeline.verifier.run_layer0_checks", return_value=layer0_result
    ), \
         patch("zsiga.pipeline.verifier.write_layer0_verify_md") as mock_write, \
         patch("zsiga.pipeline.verifier.run_layer1_pytest") as mock_l1:
        from zsiga.pipeline.verifier import verify

        result = await verify(
            agent=mock_agent,
            change_dir="/tmp/change",
            target_path="/tmp/repo",
            pre_impl_sha="abc123",
            transport=mock_transport,
        )

    assert result is None
    mock_l1.assert_not_called()
    mock_write.assert_called_once()


@pytest.mark.asyncio
async def test_verify_proceeds_to_layer1_on_layer0_pass():
    """Layer 0 PASS → verify() continues to Layer 1 pytest."""
    pass_check = Layer0Check(
        id="all", description="ok", passed=True, evidence="all good"
    )
    layer0_result = Layer0Result(checks=[pass_check], elapsed_seconds=0.01)

    mock_transport = MagicMock()
    mock_agent = MagicMock()

    # Layer 1 result mock — vacuous=False, needs_layer2=False
    mock_layer1 = MagicMock()
    mock_layer1.vacuous = False
    mock_layer1.summary_line.return_value = "L1 pass"

    with patch(
        "zsiga.pipeline.verifier.run_layer0_checks", return_value=layer0_result
    ), \
         patch("zsiga.pipeline.verifier.run_layer1_pytest", return_value=mock_layer1) as mock_l1, \
         patch("zsiga.pipeline.verifier.has_non_testable_scenarios", return_value=False), \
         patch("zsiga.pipeline.verifier._write_pure_layer1_verify_md"):
        from zsiga.pipeline.verifier import verify

        await verify(
            agent=mock_agent,
            change_dir="/tmp/change",
            target_path="/tmp/repo",
            pre_impl_sha="abc123",
            transport=mock_transport,
        )

    mock_l1.assert_called_once()
