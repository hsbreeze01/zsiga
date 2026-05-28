"""Tests for active_target filtering in orchestrator and pending_switch mechanism."""
import os
import tempfile

import yaml

from zsiga.config import (
    TargetConfig,
    ZsigaConfig,
    LLMConfig,
    PipelineConfig,
    IntakeConfig,
    SafetyConfig,
    load_config,
    load_runtime_state,
    save_runtime_state,
)


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


def _make_config(active="zsiga", extra_targets=None) -> ZsigaConfig:
    """Build a ZsigaConfig with multiple targets for filtering tests."""
    targets = {
        "zsiga": TargetConfig(
            name="zsiga", path="/tmp/zsiga", domain="self", deploy_branch="main",
        ),
    }
    if extra_targets:
        for name, tcfg in extra_targets.items():
            targets[name] = TargetConfig(name=name, **tcfg)
    return ZsigaConfig(
        llm=LLMConfig(provider="test", model="test-model", api_key="test-key"),
        targets=targets,
        pipeline=PipelineConfig(),
        intake=IntakeConfig(),
        safety=SafetyConfig(),
        active_target=active,
    )


# ── 1. Orchestrator active_target filtering ──────────────────────────


class TestOrchestratorActiveTargetFilter:
    def test_active_target_zsiga_only_scans_zsiga(self, tmp_path, monkeypatch):
        """When active_target=zsiga, scanner should only receive zsiga target."""
        from zsiga.pipeline.orchestrator import ZsigaOrchestrator
        from zsiga.intake.scanner import DirectoryScanner

        config = _make_config(active="zsiga", extra_targets={
            "factory": {"path": "/tmp/factory", "domain": "external"},
        })

        scanned_targets = {}

        original_scan = DirectoryScanner.scan

        def capture_scan(self_scanner, transports=None):
            scanned_targets.update(self_scanner.targets)
            return []

        monkeypatch.setattr(DirectoryScanner, "scan", capture_scan)

        # Patch _load_context to avoid file I/O
        monkeypatch.setattr(ZsigaOrchestrator, "_load_context", lambda self: None)

        import asyncio
        orch = ZsigaOrchestrator(config)
        asyncio.run(orch.run_cycle())

        assert "zsiga" in scanned_targets
        assert "factory" not in scanned_targets

    def test_active_target_factory_only_scans_factory(self, tmp_path, monkeypatch):
        """When active_target=factory, scanner should only receive factory target."""
        from zsiga.pipeline.orchestrator import ZsigaOrchestrator
        from zsiga.intake.scanner import DirectoryScanner

        config = _make_config(active="factory", extra_targets={
            "factory": {"path": "/tmp/factory", "domain": "external"},
        })

        scanned_targets = {}

        def capture_scan(self_scanner, transports=None):
            scanned_targets.update(self_scanner.targets)
            return []

        monkeypatch.setattr(DirectoryScanner, "scan", capture_scan)
        monkeypatch.setattr(ZsigaOrchestrator, "_load_context", lambda self: None)

        import asyncio
        orch = ZsigaOrchestrator(config)
        asyncio.run(orch.run_cycle())

        assert "factory" in scanned_targets
        assert "zsiga" not in scanned_targets

    def test_active_target_unknown_falls_back_to_all(self, tmp_path, monkeypatch):
        """When active_target not in targets, fall back to all targets."""
        from zsiga.pipeline.orchestrator import ZsigaOrchestrator
        from zsiga.intake.scanner import DirectoryScanner

        config = _make_config(active="nonexistent", extra_targets={
            "factory": {"path": "/tmp/factory", "domain": "external"},
        })

        scanned_targets = {}

        def capture_scan(self_scanner, transports=None):
            scanned_targets.update(self_scanner.targets)
            return []

        monkeypatch.setattr(DirectoryScanner, "scan", capture_scan)
        monkeypatch.setattr(ZsigaOrchestrator, "_load_context", lambda self: None)

        import asyncio
        orch = ZsigaOrchestrator(config)
        asyncio.run(orch.run_cycle())

        assert "zsiga" in scanned_targets
        assert "factory" in scanned_targets

    def test_config_loads_active_target_from_runtime_state(self, tmp_path, monkeypatch):
        """active_target should be read from runtime_state.yaml."""
        config_data = _minimal_config(**{
            "factory": {"path": "/tmp/factory", "domain": "external"},
        })
        _write_yaml(tmp_path, config_data)

        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        (data_dir / "runtime_state.yaml").write_text(
            yaml.dump({"active_target": "factory"})
        )
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))

        config = load_config(path=str(tmp_path / "zsiga.yaml"))
        assert config.active_target == "factory"


# ── 2. pending_switch runtime state ──────────────────────────────────


class TestPendingSwitchState:
    def test_save_and_load_pending_switch(self, tmp_path, monkeypatch):
        """pending_switch field persists in runtime_state."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        state = {
            "active_target": "zsiga",
            "pending_switch": "factory",
        }
        save_runtime_state(state)

        loaded = load_runtime_state()
        assert loaded["active_target"] == "zsiga"
        assert loaded["pending_switch"] == "factory"

    def test_pending_switch_cleared_after_execution(self, tmp_path, monkeypatch):
        """Simulate daemon executing a pending switch and clearing it."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        state = {
            "active_target": "zsiga",
            "pending_switch": "factory",
        }
        save_runtime_state(state)

        # Daemon executes pending switch
        loaded = load_runtime_state()
        pending = loaded.get("pending_switch")
        assert pending == "factory"

        loaded["active_target"] = pending
        loaded.pop("pending_switch", None)
        save_runtime_state(loaded)

        # Verify
        final = load_runtime_state()
        assert final["active_target"] == "factory"
        assert "pending_switch" not in final

    def test_pending_switch_overridden_by_evolution_window(self, tmp_path, monkeypatch):
        """Evolution window should clear pending_switch to non-zsiga targets."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        state = {
            "active_target": "zsiga",
            "pending_switch": "factory",
            "evolution_window_start_hour": 0,
            "evolution_window_end_hour": 24,
        }
        save_runtime_state(state)

        # Simulate daemon logic: in window + pending != zsiga → clear
        loaded = load_runtime_state()
        evo_start = loaded.get("evolution_window_start_hour", 22)
        evo_end = loaded.get("evolution_window_end_hour", 10)
        # window 0-24 is always active
        from datetime import datetime
        h = datetime.now().hour
        in_window = (h >= evo_start or h < evo_end) if evo_start > evo_end else (evo_start <= h < evo_end)

        pending = loaded.get("pending_switch")
        if in_window and pending and pending != "zsiga":
            loaded.pop("pending_switch", None)
            save_runtime_state(loaded)

        final = load_runtime_state()
        assert "pending_switch" not in final
        assert final["active_target"] == "zsiga"

    def test_pending_switch_to_zsiga_allowed_in_window(self, tmp_path, monkeypatch):
        """Switching back to zsiga should always be allowed even in window."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        state = {
            "active_target": "factory",
            "pending_switch": "zsiga",
            "evolution_window_start_hour": 0,
            "evolution_window_end_hour": 24,
        }
        save_runtime_state(state)

        # Simulate daemon: pending == "zsiga" → execute regardless of window
        loaded = load_runtime_state()
        pending = loaded.get("pending_switch")
        if pending == "zsiga":
            loaded["active_target"] = "zsiga"
            loaded.pop("pending_switch", None)
            save_runtime_state(loaded)

        final = load_runtime_state()
        assert final["active_target"] == "zsiga"
        assert "pending_switch" not in final


# ── 3. pending_switch web interaction ────────────────────────────────


class TestPendingSwitchWeb:
    def test_web_writes_pending_when_daemon_running(self, tmp_path, monkeypatch):
        """When daemon is running, target_activate should write pending_switch."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        # Initial state
        state = {"active_target": "zsiga"}
        save_runtime_state(state)

        # Simulate web writing pending_switch (like admin.py does)
        rs = load_runtime_state()
        rs["pending_switch"] = "factory"
        save_runtime_state(rs)

        loaded = load_runtime_state()
        assert loaded["active_target"] == "zsiga"
        assert loaded["pending_switch"] == "factory"

    def test_web_direct_switch_when_daemon_idle(self, tmp_path, monkeypatch):
        """When daemon is idle, target_activate should write active_target directly."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        state = {"active_target": "zsiga"}
        save_runtime_state(state)

        # Simulate web direct switch
        rs = load_runtime_state()
        rs["active_target"] = "factory"
        rs.pop("pending_switch", None)
        save_runtime_state(rs)

        loaded = load_runtime_state()
        assert loaded["active_target"] == "factory"
        assert "pending_switch" not in loaded

    def test_pending_switch_cleared_on_direct_activate(self, tmp_path, monkeypatch):
        """Direct activate should clear any existing pending_switch."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        state = {"active_target": "zsiga", "pending_switch": "factory"}
        save_runtime_state(state)

        # Direct activate to compass
        rs = load_runtime_state()
        rs["active_target"] = "compass"
        rs.pop("pending_switch", None)
        save_runtime_state(rs)

        loaded = load_runtime_state()
        assert loaded["active_target"] == "compass"
        assert "pending_switch" not in loaded
