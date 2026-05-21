"""Tests for spec: implement-prompt-injection.

Covers that the implementer's system prompt includes the learnings section
when relevant learnings exist, and omits it otherwise.
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _write_jsonl(fpath: Path, records: list[dict]):
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.fixture
def _patch_agent_run():
    """Patch AgentLoop.run to capture the system_prompt it receives."""
    captured = {}

    async def fake_run(self, system_prompt, user_prompt, **kwargs):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "fake result"

    return captured, fake_run


class TestImplementPromptInjection:
    """Verify learnings section appears in implementer system prompt."""

    def _make_records(self, count, pattern_key="pipeline.fail.implement",
                      takeaway="Never use bare except"):
        return [
            {
                "type": "lesson",
                "ts": f"2026-05-{10 - i:02d}T00:00:00",
                "source": "test",
                "title": f"lesson {i}",
                "context": "ctx",
                "takeaway": takeaway,
                "pattern_key": pattern_key,
            }
            for i in range(count)
        ]

    @pytest.mark.asyncio
    async def test_system_prompt_includes_learnings_section(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", self._make_records(2))

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.implementer.AgentLoop") as MockAgent, \
             patch("zsiga.pipeline.implementer.LocalTransport"):
            MockAgent.return_value.run = fake_run
            from zsiga.pipeline.implementer import implement
            # Create a minimal agent mock
            agent = MagicMock()
            agent.run = fake_run
            await implement(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        sp = captured.get("system_prompt", "")
        assert "## Previous Learnings (avoid repeating mistakes)" in sp

    @pytest.mark.asyncio
    async def test_system_prompt_omits_learnings_when_empty(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", [])

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.implementer.LocalTransport"):
            from zsiga.pipeline.implementer import implement
            agent = MagicMock()
            agent.run = fake_run
            await implement(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        sp = captured.get("system_prompt", "")
        assert "## Previous Learnings" not in sp

    @pytest.mark.asyncio
    async def test_learnings_section_at_most_5_entries(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", self._make_records(10))

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.implementer.LocalTransport"):
            from zsiga.pipeline.implementer import implement
            agent = MagicMock()
            agent.run = fake_run
            await implement(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        sp = captured.get("system_prompt", "")
        learnings_section = sp.split("## Previous Learnings (avoid repeating mistakes)")[-1]
        # Count bullet lines within the section (before the next ## or end)
        section_lines = []
        for line in learnings_section.split("\n"):
            if line.startswith("## ") and "Previous Learnings" not in line:
                break
            section_lines.append(line)
        bullets = [line for line in section_lines if line.strip().startswith("- [")]
        assert len(bullets) <= 5

    @pytest.mark.asyncio
    async def test_learning_entry_format(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", self._make_records(
            1, takeaway="Never use bare except"))

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.implementer.LocalTransport"):
            from zsiga.pipeline.implementer import implement
            agent = MagicMock()
            agent.run = fake_run
            await implement(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        sp = captured.get("system_prompt", "")
        assert "- [pipeline.fail.implement] Never use bare except" in sp
