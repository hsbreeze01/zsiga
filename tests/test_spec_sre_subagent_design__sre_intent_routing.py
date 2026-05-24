"""Tests for SRE intent routing spec — sre-intent-routing.md"""
import importlib


def _get_module():
    """Import intent_router (may not exist yet in early dev)."""
    try:
        return importlib.import_module("zsiga.intent_router")
    except ModuleNotFoundError:
        return None


def _get_detect_intent():
    mod = _get_module()
    if mod is None:
        return None
    return getattr(mod, "detect_intent", None)


# ---------------------------------------------------------------------------
# Scenario: Detect SRE intent from Chinese keywords
# ---------------------------------------------------------------------------
def test_detect_sre_intent_chinese_keywords():
    detect = _get_detect_intent()
    if detect is None:
        import pytest
        pytest.skip("zsiga.intent_router not yet implemented")
    result = detect("服务重启失败了")
    assert result == "sre", f"Expected 'sre' for Chinese SRE input, got {result!r}"


# ---------------------------------------------------------------------------
# Scenario: Detect SRE intent from English keywords
# ---------------------------------------------------------------------------
def test_detect_sre_intent_english_keywords():
    detect = _get_detect_intent()
    if detect is None:
        import pytest
        pytest.skip("zsiga.intent_router not yet implemented")
    result = detect("check disk usage on the server")
    assert result == "sre", f"Expected 'sre' for English SRE input, got {result!r}"


# ---------------------------------------------------------------------------
# Scenario: SRE keywords take precedence over ambiguous input
# ---------------------------------------------------------------------------
def test_sre_takes_precedence_over_code():
    detect = _get_detect_intent()
    if detect is None:
        import pytest
        pytest.skip("zsiga.intent_router not yet implemented")
    result = detect("磁盘满了，修复代码里的日志写入逻辑")
    assert result == "sre", f"Expected 'sre' for mixed input with SRE keyword, got {result!r}"


# ---------------------------------------------------------------------------
# Scenario: Pure code input returns code intent
# ---------------------------------------------------------------------------
def test_pure_code_returns_code_intent():
    detect = _get_detect_intent()
    if detect is None:
        import pytest
        pytest.skip("zsiga.intent_router not yet implemented")
    result = detect("修复这个函数的bug")
    assert result == "code", f"Expected 'code' for pure code input, got {result!r}"


# ---------------------------------------------------------------------------
# Scenario: Unrecognized input defaults to code intent
# ---------------------------------------------------------------------------
def test_unrecognized_defaults_to_code():
    detect = _get_detect_intent()
    if detect is None:
        import pytest
        pytest.skip("zsiga.intent_router not yet implemented")
    result = detect("你好")
    assert result == "code", f"Expected 'code' for unrecognized input, got {result!r}"


# ---------------------------------------------------------------------------
# Scenario: SRE keywords are accessible as a module constant
# ---------------------------------------------------------------------------
def test_sre_keywords_constant_exists():
    mod = _get_module()
    if mod is None:
        import pytest
        pytest.skip("zsiga.intent_router not yet implemented")
    keywords = getattr(mod, "SRE_KEYWORDS", None)
    assert keywords is not None, "SRE_KEYWORDS constant must exist in intent_router"
    required = {"服务", "重启", "健康", "清理", "磁盘", "宕机", "日志", "进程", "监控"}
    keyword_set = set(keywords)
    missing = required - keyword_set
    assert not missing, f"SRE_KEYWORDS missing required keywords: {missing}"
