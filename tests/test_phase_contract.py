from __future__ import annotations

from pathlib import Path

from zsiga.harness.phase_contract import PhaseContractHarness
from zsiga.transport import LocalTransport


def _change_dir(tmp_path: Path) -> Path:
    change = tmp_path / "openspec" / "changes" / "demo-change"
    (change / "specs" / "capability").mkdir(parents=True)
    return change


def _write_enriched(change: Path) -> None:
    (change / "proposal.md").write_text("# Proposal\n")
    (change / "clarify.md").write_text(
        "# Clarify\n\n## 需求拆解\n- a\n## 边界\n- b\n## 目标\n- c\n## 约束\n- d\n"
    )
    (change / "design.md").write_text("# Design\n")
    (change / "tasks.md").write_text("- [ ] implement\n")
    (change / "specs" / "capability" / "spec.md").write_text("# Spec\n")


def _validate(tmp_path: Path, change: Path, phase: str, **context):
    return PhaseContractHarness().validate(
        phase,
        change_dir=str(change),
        target_path=str(tmp_path),
        project="zsiga",
        active_target="zsiga",
        transport=LocalTransport(),
        context=context or None,
    )


def test_clarify_contract_requires_output_sections(tmp_path: Path) -> None:
    change = _change_dir(tmp_path)
    (change / "proposal.md").write_text("# Proposal\n")
    (change / "clarify.md").write_text("## 需求拆解\n")

    result = _validate(tmp_path, change, "clarify")

    assert not result.passed
    assert any("边界" in v.message for v in result.violations)


def test_enrich_contract_accepts_complete_artifacts(tmp_path: Path) -> None:
    change = _change_dir(tmp_path)
    _write_enriched(change)

    result = _validate(tmp_path, change, "enrich")

    assert result.passed


def test_enrich_contract_fails_without_specs(tmp_path: Path) -> None:
    change = _change_dir(tmp_path)
    _write_enriched(change)
    (change / "specs" / "capability" / "spec.md").unlink()

    result = _validate(tmp_path, change, "enrich")

    assert not result.passed
    assert any("specs" in v.field for v in result.violations)


def test_contract_fails_when_project_is_not_active_target(tmp_path: Path) -> None:
    change = _change_dir(tmp_path)
    _write_enriched(change)

    result = PhaseContractHarness().validate(
        "enrich",
        change_dir=str(change),
        target_path=str(tmp_path),
        project="external-a",
        active_target="zsiga",
        transport=LocalTransport(),
    )

    assert not result.passed
    assert any(v.field == "active_target" for v in result.violations)


def test_implement_contract_requires_committed_diff(tmp_path: Path) -> None:
    change = _change_dir(tmp_path)
    _write_enriched(change)
    transport = LocalTransport()
    transport.run_shell("git init -q", cwd=str(tmp_path))
    transport.run_shell("git config user.email test@example.com", cwd=str(tmp_path))
    transport.run_shell("git config user.name Tester", cwd=str(tmp_path))
    (tmp_path / "README.md").write_text("before\n")
    transport.run_shell("git add README.md && git commit -q -m init", cwd=str(tmp_path))
    pre_sha = transport.run_shell("git rev-parse HEAD", cwd=str(tmp_path))["stdout"].strip()
    (tmp_path / "README.md").write_text("after\n")
    transport.run_shell("git add README.md && git commit -q -m change", cwd=str(tmp_path))

    result = _validate(tmp_path, change, "implement", pre_sha=pre_sha)

    assert result.passed


def test_verify_contract_requires_verdict(tmp_path: Path) -> None:
    change = _change_dir(tmp_path)
    (change / "verify.md").write_text("No decision yet\n")

    result = _validate(tmp_path, change, "verify")

    assert not result.passed
    assert any("Verdict" in v.message for v in result.violations)
