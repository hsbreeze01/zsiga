"""Tests for validate_config high-complexity branch coverage.

Spec: config-validate
Change: evo-improvement-20260530-045307
"""

from zsiga.config import (
    LLMConfig,
    PipelineConfig,
    TargetConfig,
    ZsigaConfig,
    validate_config,
    IntakeConfig,
    SafetyConfig,
)


def _make_config(**overrides) -> ZsigaConfig:
    """Build a valid ZsigaConfig with sensible defaults, allowing overrides."""
    llm = overrides.get(
        "llm",
        LLMConfig(provider="openai", model="gpt-4", api_key="sk-test-key"),
    )
    targets = overrides.get(
        "targets",
        {"default": TargetConfig(name="default", path="/tmp/project", transport="local")},
    )
    pipeline = overrides.get("pipeline", PipelineConfig())
    intake = overrides.get("intake", IntakeConfig())
    safety = overrides.get("safety", SafetyConfig())
    return ZsigaConfig(
        llm=llm, targets=targets, pipeline=pipeline, intake=intake, safety=safety
    )


class TestValidateDomainWarning:
    """Scenario: Warning for unrecognized domain value."""

    def test_unrecognized_domain_produces_warning(self):
        config = _make_config(
            targets={
                "t": TargetConfig(
                    name="t", path="/p", transport="local", domain="production"
                ),
            }
        )
        result = validate_config(config)
        assert result.valid is True
        assert any("domain" in w and "t" in w for w in result.warnings)

    def test_self_domain_no_warning(self):
        config = _make_config(
            targets={
                "t": TargetConfig(
                    name="t", path="/p", transport="local", domain="self"
                ),
            }
        )
        result = validate_config(config)
        assert not any("domain" in w for w in result.warnings)

    def test_external_domain_no_warning(self):
        config = _make_config(
            targets={
                "t": TargetConfig(
                    name="t", path="/p", transport="local", domain="external"
                ),
            }
        )
        result = validate_config(config)
        assert not any("domain" in w for w in result.warnings)


class TestValidateFixAttemptsUpperBound:
    """Scenario: Warning for fix_attempts above range."""

    def test_fix_attempts_above_20(self):
        config = _make_config(pipeline=PipelineConfig(fix_attempts=25))
        result = validate_config(config)
        assert result.valid is True
        assert any("fix_attempts" in w for w in result.warnings)

    def test_fix_attempts_at_20_no_warning(self):
        config = _make_config(pipeline=PipelineConfig(fix_attempts=20))
        result = validate_config(config)
        assert not any("fix_attempts" in w for w in result.warnings)


class TestValidateMultipleErrorsAccumulated:
    """Scenario: Multiple LLM field errors reported together."""

    def test_three_llm_errors(self):
        config = _make_config(
            llm=LLMConfig(provider="", model="", api_key="")
        )
        result = validate_config(config)
        assert result.valid is False
        # provider, model, api_key each produce one error
        assert len(result.errors) >= 3
        assert any("provider" in e for e in result.errors)
        assert any("model" in e for e in result.errors)
        assert any("api_key" in e for e in result.errors)

    def test_missing_llm_fields_plus_no_targets(self):
        config = _make_config(
            llm=LLMConfig(provider="", model="", api_key=""),
            targets={},
        )
        result = validate_config(config)
        assert len(result.errors) >= 4  # 3 LLM + 1 targets


class TestValidateMaxChangesPerCycleBoundary:
    """Scenario: Boundary value 1 and 10 produce no warning."""

    def test_boundary_1_no_warning(self):
        config = _make_config(pipeline=PipelineConfig(max_changes_per_cycle=1))
        result = validate_config(config)
        assert not any("max_changes_per_cycle" in w for w in result.warnings)

    def test_boundary_10_no_warning(self):
        config = _make_config(pipeline=PipelineConfig(max_changes_per_cycle=10))
        result = validate_config(config)
        assert not any("max_changes_per_cycle" in w for w in result.warnings)


class TestValidateTemperatureBoundary:
    """Scenario: Temperature at lower/upper boundary produces no warning."""

    def test_temperature_at_0(self):
        config = _make_config(
            llm=LLMConfig(provider="openai", model="gpt-4", api_key="sk-test", temperature=0.0)
        )
        result = validate_config(config)
        assert not any("temperature" in w for w in result.warnings)

    def test_temperature_at_2(self):
        config = _make_config(
            llm=LLMConfig(provider="openai", model="gpt-4", api_key="sk-test", temperature=2.0)
        )
        result = validate_config(config)
        assert not any("temperature" in w for w in result.warnings)
