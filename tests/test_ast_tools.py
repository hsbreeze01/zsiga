import os
import tempfile
from pathlib import Path

from zsiga.agent.ast_tools import ast_search, ast_replace, _detect_lang
from zsiga.transport import LocalTransport


def _make_file(tmpdir: str, filename: str, content: str) -> str:
    p = Path(tmpdir) / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return filename


def test_detect_lang():
    assert _detect_lang("foo.py") == "python"
    assert _detect_lang("bar.js") == "javascript"
    assert _detect_lang("baz.rs") == "rust"
    assert _detect_lang("unknown.txt") is None


def test_ast_search_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_file(tmpdir, "app.py", "def foo(x):\n    return x + 1\n")
        t = LocalTransport()
        result = ast_search(t, tmpdir, pattern="return $X", path="app.py")
        assert result["matches"] == 1
        assert result["results"][0]["text"] == "return x + 1"
        assert result["lang"] == "python"


def test_ast_search_no_matches():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_file(tmpdir, "app.py", "x = 1\n")
        t = LocalTransport()
        result = ast_search(t, tmpdir, pattern="def $NAME($ARGS)", path="app.py")
        assert result["matches"] == 0
        assert result["results"] == []


def test_ast_search_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        t = LocalTransport()
        result = ast_search(t, tmpdir, pattern="return $X", path="nope.py")
        assert "error" in result


def test_ast_search_unknown_lang():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_file(tmpdir, "data.csv", "a,b,c\n")
        t = LocalTransport()
        result = ast_search(t, tmpdir, pattern="$X", path="data.csv")
        assert "error" in result
        assert "Cannot detect language" in result["error"]


def test_ast_search_explicit_lang():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_file(tmpdir, "app.py", "def foo(x):\n    return x + 1\n")
        t = LocalTransport()
        result = ast_search(t, tmpdir, pattern="return $X", path="app.py", lang="python")
        assert result["matches"] == 1


def test_ast_search_multiple_matches():
    with tempfile.TemporaryDirectory() as tmpdir:
        code = "def foo(x):\n    return x + 1\n\ndef bar(y):\n    return y * 2\n"
        _make_file(tmpdir, "app.py", code)
        t = LocalTransport()
        result = ast_search(t, tmpdir, pattern="def $NAME($ARGS)", path="app.py")
        assert result["matches"] == 2


def test_ast_replace_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_file(tmpdir, "app.py", "def foo(x):\n    return x + 1\n")
        t = LocalTransport()
        result = ast_replace(t, tmpdir, pattern="return $X", replacement="return 42", path="app.py")
        assert result["ok"] is True
        assert result["matches_replaced"] == 1

        content = (Path(tmpdir) / "app.py").read_text()
        assert "return 42" in content
        assert "return x + 1" not in content


def test_ast_replace_no_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_file(tmpdir, "app.py", "x = 1\n")
        t = LocalTransport()
        result = ast_replace(t, tmpdir, pattern="def $NAME($ARGS)", replacement="pass", path="app.py")
        assert "error" in result
        assert result["matches"] == 0


def test_ast_replace_preserves_surrounding():
    with tempfile.TemporaryDirectory() as tmpdir:
        code = "import os\n\ndef foo(x):\n    return x + 1\n\ndef bar():\n    pass\n"
        _make_file(tmpdir, "app.py", code)
        t = LocalTransport()
        result = ast_replace(t, tmpdir, pattern="return $X", replacement="return 0", path="app.py")
        assert result["ok"] is True
        content = (Path(tmpdir) / "app.py").read_text()
        assert "import os" in content
        assert "def bar" in content
        assert "return 0" in content


def test_ast_replace_multiple():
    with tempfile.TemporaryDirectory() as tmpdir:
        code = "def foo(x):\n    return x + 1\n\ndef bar(y):\n    return y * 2\n"
        _make_file(tmpdir, "app.py", code)
        t = LocalTransport()
        result = ast_replace(t, tmpdir, pattern="return $X", replacement="return 42", path="app.py")
        assert result["ok"] is True
        assert result["matches_replaced"] == 2
        content = (Path(tmpdir) / "app.py").read_text()
        assert content.count("return 42") == 2
