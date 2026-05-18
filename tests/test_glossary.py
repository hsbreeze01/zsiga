"""Tests for glossary extraction, caching, and loading."""
import json
from datetime import datetime, timedelta

from zsiga.pipeline.glossary import (
    Glossary, GlossaryEntry, extract_glossary, load_glossary,
)
from zsiga.transport import LocalTransport


class TestGlossaryDataclass:
    def test_summary_empty(self):
        g = Glossary(project="test", extracted_at="2024-01-01T00:00:00")
        assert g.summary() == ""

    def test_summary_groups_by_category(self):
        g = Glossary(
            project="test",
            extracted_at="2024-01-01T00:00:00",
            entries=[
                GlossaryEntry(name="Foo", category="class", file="a.py"),
                GlossaryEntry(name="Bar", category="class", file="b.py"),
                GlossaryEntry(name="do_stuff", category="function", file="c.py"),
            ],
        )
        result = g.summary()
        assert "## Domain Glossary" in result
        assert "**class**" in result
        assert "**function**" in result
        assert "Foo" in result
        assert "Bar" in result
        assert "do_stuff" in result

    def test_summary_respects_top_n(self):
        entries = [GlossaryEntry(name=f"Item{i}", category="class", file="a.py")
                   for i in range(50)]
        g = Glossary(project="test", extracted_at="2024-01-01T00:00:00",
                     entries=entries)
        result = g.summary(top_n=10)
        assert "Item9" in result
        assert "Item10" not in result


class TestGlossaryExtraction:
    def test_extract_from_sample_project(self, tmp_path):
        src = tmp_path / "myproject"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "app.py").write_text(
            "class App:\n"
            "    pass\n"
            "\n"
            "def run_server():\n"
            "    pass\n"
            "\n"
            "DEBUG = True\n"
            "\n"
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            "@app.route('/api/v1/test')\n"
            "def test_route():\n"
            "    pass\n"
        )
        g = extract_glossary(str(src))
        assert g.project == "myproject"
        names = [e.name for e in g.entries]
        assert "App" in names
        assert "run_server" in names
        assert "/api/v1/test" in names
        assert "DEBUG" in names

    def test_extract_skips_underscore_functions(self, tmp_path):
        src = tmp_path / "proj"
        src.mkdir()
        (src / "mod.py").write_text(
            "def public_func():\n    pass\n\ndef _private_func():\n    pass\n"
        )
        g = extract_glossary(str(src))
        names = [e.name for e in g.entries]
        assert "public_func" in names
        assert "_private_func" not in names

    def test_persists_to_cache(self, tmp_path):
        src = tmp_path / "cached_proj"
        src.mkdir()
        (src / "main.py").write_text("class Main:\n    pass\n")
        # Override glossary dir for testing
        import zsiga.pipeline.glossary as gmod
        original_dir = gmod._GLOSSARY_DIR
        gmod._GLOSSARY_DIR = tmp_path / "glossary_cache"
        try:
            extract_glossary(str(src))
            cache_file = tmp_path / "glossary_cache" / "cached_proj.json"
            assert cache_file.exists()
            data = json.loads(cache_file.read_text())
            assert data["project"] == "cached_proj"
            assert len(data["entries"]) > 0
        finally:
            gmod._GLOSSARY_DIR = original_dir


class TestGlossaryLoading:
    def test_load_fresh_cache(self, tmp_path):
        import zsiga.pipeline.glossary as gmod
        original_dir = gmod._GLOSSARY_DIR
        gmod._GLOSSARY_DIR = tmp_path / "glossary_cache"
        try:
            cache_dir = tmp_path / "glossary_cache"
            cache_dir.mkdir(parents=True)
            now = datetime.now().isoformat()
            data = {
                "project": "fresh_proj",
                "extracted_at": now,
                "entries": [{"name": "Foo", "category": "class", "file": "a.py"}],
            }
            (cache_dir / "fresh_proj.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            g = load_glossary("fresh_proj")
            assert g is not None
            assert len(g.entries) == 1
            assert g.entries[0].name == "Foo"
        finally:
            gmod._GLOSSARY_DIR = original_dir

    def test_load_expired_cache_reextracts(self, tmp_path):
        import zsiga.pipeline.glossary as gmod
        original_dir = gmod._GLOSSARY_DIR
        gmod._GLOSSARY_DIR = tmp_path / "glossary_cache"
        try:
            cache_dir = tmp_path / "glossary_cache"
            cache_dir.mkdir(parents=True)
            old_time = (datetime.now() - timedelta(hours=25)).isoformat()
            data = {
                "project": "old_proj",
                "extracted_at": old_time,
                "entries": [{"name": "OldClass", "category": "class", "file": "a.py"}],
            }
            (cache_dir / "old_proj.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            # Create a project dir to extract from
            src = tmp_path / "old_proj"
            src.mkdir()
            (src / "main.py").write_text("class NewClass:\n    pass\n")
            g = load_glossary("old_proj", target_path=str(src))
            assert g is not None
            names = [e.name for e in g.entries]
            assert "NewClass" in names
        finally:
            gmod._GLOSSARY_DIR = original_dir

    def test_load_no_cache_no_target(self, tmp_path):
        import zsiga.pipeline.glossary as gmod
        original_dir = gmod._GLOSSARY_DIR
        gmod._GLOSSARY_DIR = tmp_path / "glossary_empty"
        try:
            g = load_glossary("nonexistent")
            assert g is None
        finally:
            gmod._GLOSSARY_DIR = original_dir


class TestGlossaryIntegration:
    def test_glossary_section_in_project_context(self, tmp_path):
        from zsiga.pipeline.project_context import _glossary_section
        import zsiga.pipeline.glossary as gmod
        original_dir = gmod._GLOSSARY_DIR
        gmod._GLOSSARY_DIR = tmp_path / "glossary_cache"
        try:
            src = tmp_path / "integration_proj"
            src.mkdir()
            (src / "app.py").write_text("class MyApp:\n    pass\n")
            result = _glossary_section(str(src), LocalTransport())
            assert "## Domain Glossary" in result
            assert "MyApp" in result
        finally:
            gmod._GLOSSARY_DIR = original_dir
