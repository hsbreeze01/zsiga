"""Tests for spec: enrich-prompt-injection.

Covers that the enricher's prompt includes the learnings section
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
    """Patch AgentLoop.run to capture prompts."""
    captured = {}

    async def fake_run(self, system_prompt, user_prompt, **kwargs):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "fake result"

    return captured, fake_run


class TestEnrichPromptInjection:
    """Verify learnings section appears in enricher prompt."""

    def _make_records(self, count, pattern_key="pipeline.fail.implement",
                      takeaway="Success"):
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
    async def test_prompt_includes_learnings_section(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", self._make_records(2))

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.enricher.LocalTransport"):
            from zsiga.pipeline.enricher import enrich
            agent = MagicMock()
            agent.run = fake_run
            await enrich(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        combined = captured.get("system_prompt", "") + captured.get("user_prompt", "")
        assert "## Relevant Past Experience" in combined

    @pytest.mark.asyncio
    async def test_prompt_omits_learnings_when_empty(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", [])

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.enricher.LocalTransport"):
            from zsiga.pipeline.enricher import enrich
            agent = MagicMock()
            agent.run = fake_run
            await enrich(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        combined = captured.get("system_prompt", "") + captured.get("user_prompt", "")
        assert "## Relevant Past Experience" not in combined

    @pytest.mark.asyncio
    async def test_learnings_section_at_most_3_entries(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", self._make_records(10))

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.enricher.LocalTransport"):
            from zsiga.pipeline.enricher import enrich
            agent = MagicMock()
            agent.run = fake_run
            await enrich(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        combined = captured.get("system_prompt", "") + captured.get("user_prompt", "")
        learnings_section = combined.split("## Relevant Past Experience")[-1]
        section_lines = []
        for line in learnings_section.split("\n"):
            if line.startswith("## ") and "Relevant Past Experience" not in line:
                break
            section_lines.append(line)
        bullets = [line for line in section_lines if line.strip().startswith("- [")]
        assert len(bullets) <= 3

    @pytest.mark.asyncio
    async def test_learning_entry_format(self, tmp_path, _patch_agent_run):
        captured, fake_run = _patch_agent_run
        _write_jsonl(tmp_path / "learnings.jsonl", self._make_records(
            1, pattern_key="pipeline.pass.deliver", takeaway="Success"))

        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path), \
             patch("zsiga.pipeline.enricher.LocalTransport"):
            from zsiga.pipeline.enricher import enrich
            agent = MagicMock()
            agent.run = fake_run
            await enrich(
                agent, change_dir=str(tmp_path / "change"),
                target_path=str(tmp_path / "target"),
            )

        combined = captured.get("system_prompt", "") + captured.get("user_prompt", "")
        assert "- [pipeline.pass.deliver] Success" in combined
