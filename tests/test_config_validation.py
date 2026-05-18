import pytest

from zsiga.config import (
    ConfigValidationError,
    LLMConfig,
    PipelineConfig,
    SSHConfig,
    SafetyConfig,
    TargetConfig,
    IntakeConfig,
    ValidationResult,
    ZsigaConfig,
    validate_config,
)


def _make_config(**overrides) -> ZsigaConfig:
    """Build a valid ZsigaConfig with sensible defaults, allowing overrides."""
    llm = overrides.get("llm", LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="sk-test-key",
    ))
    targets = overrides.get("targets", {
        "default": TargetConfig(
            name="default",
            path="/tmp/project",
            transport="local",
        ),
    })
    pipeline = overrides.get("pipeline", PipelineConfig())
    intake = overrides.get("intake", IntakeConfig())
    safety = overrides.get("safety", SafetyConfig())
    return ZsigaConfig(llm=llm, targets=targets, pipeline=pipeline,
                       intake=intake, safety=safety)


class TestValidationResult:
    def test_valid_when_no_errors(self):
        r = ValidationResult(errors=[], warnings=["something"])
        assert r.valid is True

    def test_invalid_when_errors_present(self):
        r = ValidationResult(errors=["bad"], warnings=[])
        assert r.valid is False

    def test_valid_with_no_warnings(self):
        r = ValidationResult()
        assert r.valid is True
        assert r.errors == []
        assert r.warnings == []


class TestValidConfig:
    def test_all_fields_valid(self):
        config = _make_config()
        result = validate_config(config)
        assert result.valid is True
        assert result.errors == []
        # May have warnings but should be empty for defaults
        assert result.warnings == []


class TestMissingLLMFields:
    def test_missing_provider(self):
        config = _make_config(llm=LLMConfig(
            provider="", model="gpt-4", api_key="sk-test",
        ))
        result = validate_config(config)
        assert result.valid is False
        assert any("provider" in e for e in result.errors)

    def test_missing_model(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="", api_key="sk-test",
        ))
        result = validate_config(config)
        assert result.valid is False
        assert any("model" in e for e in result.errors)

    def test_missing_api_key(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key="",
        ))
        result = validate_config(config)
        assert result.valid is False
        assert any("api_key" in e for e in result.errors)

    def test_none_provider(self):
        config = _make_config(llm=LLMConfig(
            provider=None, model="gpt-4", api_key="sk-test",
        ))
        result = validate_config(config)
        assert result.valid is False

    def test_none_model(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model=None, api_key="sk-test",
        ))
        result = validate_config(config)
        assert result.valid is False

    def test_none_api_key(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key=None,
        ))
        result = validate_config(config)
        assert result.valid is False


class TestTemperatureWarning:
    def test_temperature_too_high(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key="sk-test",
            temperature=5.0,
        ))
        result = validate_config(config)
        assert result.valid is True
        assert any("temperature" in w for w in result.warnings)

    def test_temperature_negative(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key="sk-test",
            temperature=-1.0,
        ))
        result = validate_config(config)
        assert result.valid is True
        assert any("temperature" in w for w in result.warnings)

    def test_temperature_in_range_no_warning(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key="sk-test",
            temperature=1.5,
        ))
        result = validate_config(config)
        assert not any("temperature" in w for w in result.warnings)


class TestMaxTokensWarning:
    def test_max_tokens_zero(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key="sk-test",
            max_tokens=0,
        ))
        result = validate_config(config)
        assert result.valid is True
        assert any("max_tokens" in w for w in result.warnings)

    def test_max_tokens_negative(self):
        config = _make_config(llm=LLMConfig(
            provider="openai", model="gpt-4", api_key="sk-test",
            max_tokens=-100,
        ))
        result = validate_config(config)
        assert result.valid is True
        assert any("max_tokens" in w for w in result.warnings)


class TestTargetValidation:
    def test_no_targets(self):
        config = _make_config(targets={})
        result = validate_config(config)
        assert result.valid is False
        assert any("target" in e.lower() for e in result.errors)

    def test_empty_target_path(self):
        config = _make_config(targets={
            "bad": TargetConfig(name="bad", path="", transport="local"),
        })
        result = validate_config(config)
        assert result.valid is False
        assert any("path" in e for e in result.errors)

    def test_invalid_transport(self):
        config = _make_config(targets={
            "bad": TargetConfig(name="bad", path="/tmp", transport="ftp"),
        })
        result = validate_config(config)
        assert result.valid is False
        assert any("transport" in e for e in result.errors)

    def test_ssh_without_ssh_config(self):
        config = _make_config(targets={
            "ssh-target": TargetConfig(
                name="ssh-target", path="/tmp", transport="ssh", ssh=None,
            ),
        })
        result = validate_config(config)
        assert result.valid is False
        assert any("SSH" in e for e in result.errors)

    def test_ssh_with_empty_host(self):
        config = _make_config(targets={
            "ssh-target": TargetConfig(
                name="ssh-target", path="/tmp", transport="ssh",
                ssh=SSHConfig(host=""),
            ),
        })
        result = validate_config(config)
        assert result.valid is False
        assert any("SSH" in e for e in result.errors)

    def test_ssh_with_valid_config(self):
        config = _make_config(targets={
            "ssh-target": TargetConfig(
                name="ssh-target", path="/tmp", transport="ssh",
                ssh=SSHConfig(host="example.com"),
            ),
        })
        result = validate_config(config)
        assert result.valid is True


class TestPipelineWarnings:
    def test_max_changes_per_cycle_zero(self):
        config = _make_config(pipeline=PipelineConfig(max_changes_per_cycle=0))
        result = validate_config(config)
        assert result.valid is True
        assert any("max_changes_per_cycle" in w for w in result.warnings)

    def test_max_changes_per_cycle_too_high(self):
        config = _make_config(pipeline=PipelineConfig(max_changes_per_cycle=15))
        result = validate_config(config)
        assert result.valid is True
        assert any("max_changes_per_cycle" in w for w in result.warnings)

    def test_fix_attempts_zero(self):
        config = _make_config(pipeline=PipelineConfig(fix_attempts=0))
        result = validate_config(config)
        assert result.valid is True
        assert any("fix_attempts" in w for w in result.warnings)

    def test_enrich_max_turns_zero(self):
        config = _make_config(pipeline=PipelineConfig(enrich_max_turns=0))
        result = validate_config(config)
        assert result.valid is True
        assert any("enrich_max_turns" in w for w in result.warnings)

    def test_impl_max_turns_zero(self):
        config = _make_config(pipeline=PipelineConfig(impl_max_turns=0))
        result = validate_config(config)
        assert result.valid is True
        assert any("impl_max_turns" in w for w in result.warnings)


class TestConfigValidationError:
    def test_error_message_format(self):
        result = ValidationResult(
            errors=["error one", "error two"],
            warnings=["a warning"],
        )
        exc = ConfigValidationError(result)
        assert "error one" in str(exc)
        assert "error two" in str(exc)
        assert exc.result is result

    def test_error_holds_result(self):
        result = ValidationResult(errors=["bad"], warnings=[])
        exc = ConfigValidationError(result)
        assert exc.result.errors == ["bad"]


class TestLoadConfigIntegration:
    def test_load_config_with_validation_errors(self, tmp_path):
        config_file = tmp_path / "zsiga.yaml"
        config_file.write_text("""
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: ""
targets:
  default:
    path: /tmp/test
    transport: local
""")
        from zsiga.config import load_config
        with pytest.raises(ConfigValidationError) as exc_info:
            load_config(path=str(config_file))
        assert any("api_key" in e for e in exc_info.value.result.errors)

    def test_load_config_with_warnings_only(self, tmp_path, capsys):
        config_file = tmp_path / "zsiga.yaml"
        config_file.write_text("""
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: sk-test
    temperature: 5.0
targets:
  default:
    path: /tmp/test
    transport: local
""")
        from zsiga.config import load_config
        config = load_config(path=str(config_file))
        assert config is not None
        captured = capsys.readouterr()
        assert "temperature" in captured.err

    def test_load_valid_config(self, tmp_path):
        config_file = tmp_path / "zsiga.yaml"
        config_file.write_text("""
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: sk-test
targets:
  default:
    path: /tmp/test
    transport: local
""")
        from zsiga.config import load_config
        config = load_config(path=str(config_file))
        assert config.llm.provider == "openai"
