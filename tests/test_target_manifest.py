"""Tests for TargetConfig manifest fields and context injection."""
import os
import tempfile

import yaml

from zsiga.config import TargetConfig, load_config, validate_config
from zsiga.memory.context import _build_base_context, update_active_context


def _write_yaml(tmp_path, data: dict) -> str:
    p = tmp_path / "zsiga.yaml"
    p.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return str(p)


def _minimal_config(**target_overrides) -> dict:
    targets = {
        "zsiga": {
            "domain": "self",
            "path": "/tmp/zsiga",
            "deploy_branch": "main",
            "transport": "local",
        }
    }
    targets.update(target_overrides or {})
    return {
        "agent": {
            "llm": {
                "provider": "test",
                "model": "test-model",
                "api_key": "test-key",
            }
        },
        "targets": targets,
    }


class TestTargetConfigManifest:
    def test_domain_field_defaults_empty(self):
        tc = TargetConfig(name="test", path="/tmp/test")
        assert tc.domain == ""
        assert tc.description == ""
        assert tc.tech_stack == []
        assert tc.key_dirs == []
        assert tc.conventions == ""

    def test_domain_field_self(self):
        tc = TargetConfig(name="zsiga", path="/home/zsiga/repo", domain="self")
        assert tc.domain == "self"

    def test_domain_field_external(self):
        tc = TargetConfig(
            name="d8q-datafactory",
            path="/home/user/d8q-datafactory",
            domain="external",
            description="数据工厂服务",
            tech_stack=["python", "fastapi"],
            key_dirs=["api/routes", "services"],
            conventions="REST API uses fastapi",
        )
        assert tc.domain == "external"
        assert tc.description == "数据工厂服务"
        assert tc.tech_stack == ["python", "fastapi"]
        assert tc.key_dirs == ["api/routes", "services"]
        assert tc.conventions == "REST API uses fastapi"


class TestLoadConfigManifest:
    def test_load_config_parses_manifest_fields(self, tmp_path):
        config_data = _minimal_config(**{
            "d8q-factory": {
                "domain": "external",
                "path": "/home/user/factory",
                "transport": "local",
                "description": "数据工厂",
                "tech_stack": ["python", "fastapi", "postgresql"],
                "key_dirs": ["api/routes", "services"],
                "conventions": "REST API with fastapi",
            }
        })
        path = _write_yaml(tmp_path, config_data)
        config = load_config(path=path)

        assert "d8q-factory" in config.targets
        t = config.targets["d8q-factory"]
        assert t.domain == "external"
        assert t.description == "数据工厂"
        assert t.tech_stack == ["python", "fastapi", "postgresql"]
        assert t.key_dirs == ["api/routes", "services"]
        assert t.conventions == "REST API with fastapi"

    def test_load_config_backward_compatible(self, tmp_path):
        config_data = _minimal_config(**{
            "legacy-project": {
                "path": "/home/user/legacy",
            }
        })
        path = _write_yaml(tmp_path, config_data)
        config = load_config(path=path)

        t = config.targets["legacy-project"]
        assert t.domain == ""
        assert t.description == ""
        assert t.tech_stack == []
        assert t.key_dirs == []
        assert t.conventions == ""

    def test_validate_config_warns_bad_domain(self, tmp_path):
        config_data = _minimal_config(**{
            "bad": {"path": "/tmp/bad", "domain": "invalid"},
        })
        path = _write_yaml(tmp_path, config_data)
        config = load_config(path=path)
        result = validate_config(config)
        assert any("domain should be" in w for w in result.warnings)


class TestManifestContextInjection:
    def test_external_target_manifest_in_context(self, tmp_path, monkeypatch):
        config_data = _minimal_config(**{
            "d8q-factory": {
                "domain": "external",
                "path": "/home/user/factory",
                "transport": "local",
                "description": "数据工厂服务",
                "tech_stack": ["python", "fastapi"],
                "key_dirs": ["api/routes"],
                "conventions": "fastapi + pydantic",
            }
        })
        path = _write_yaml(tmp_path, config_data)
        monkeypatch.setenv("ZSIGA_CONFIG_PATH", path)

        import zsiga.config as cfg_mod
        original_load = cfg_mod.load_config

        def patched_load(p=None):
            return original_load(path=path)

        monkeypatch.setattr(cfg_mod, "load_config", patched_load)

        ctx = _build_base_context()
        assert "d8q-factory" in ctx
        assert "数据工厂服务" in ctx
        assert "python, fastapi" in ctx
        assert "api/routes" in ctx

    def test_self_target_no_manifest_in_context(self, tmp_path, monkeypatch):
        config_data = _minimal_config()
        path = _write_yaml(tmp_path, config_data)

        import zsiga.config as cfg_mod
        original_load = cfg_mod.load_config

        def patched_load(p=None):
            return original_load(path=path)

        monkeypatch.setattr(cfg_mod, "load_config", patched_load)

        ctx = _build_base_context()
        assert "## Target:" not in ctx
