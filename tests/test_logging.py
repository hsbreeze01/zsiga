"""Tests for zsiga.logging — TextFormatter, JsonFormatter, setup_logging, LoggingConfig."""

import json
import logging
import os
import tempfile

from zsiga.logging import JsonFormatter, LoggingConfig, TextFormatter, setup_logging


# ---------------------------------------------------------------------------
# TextFormatter
# ---------------------------------------------------------------------------

class TestTextFormatter:
    def test_phase_prefix(self):
        """TextFormatter prepends  [phase]  when phase is in extra."""
        fmt = TextFormatter()
        record = logging.LogRecord(
            name="zsiga.agent.loop",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="starting",
            args=(),
            exc_info=None,
        )
        record.phase = "enrich"
        output = fmt.format(record)
        assert output == "  [enrich] starting"

    def test_no_phase(self):
        """TextFormatter falls back to plain message when no phase."""
        fmt = TextFormatter()
        record = logging.LogRecord(
            name="zsiga.pipeline.orchestrator",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="cycle complete",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert output == "cycle complete"

    def test_preserves_emoji(self):
        """TextFormatter keeps emoji in the message text."""
        fmt = TextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="✅ done",
            args=(),
            exc_info=None,
        )
        record.phase = "impl"
        output = fmt.format(record)
        assert "  [impl] ✅ done" == output


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------

class TestJsonFormatter:
    def test_valid_json(self):
        """JsonFormatter produces valid JSON."""
        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="zsiga.agent.loop",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="starting",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        obj = json.loads(output)
        assert "timestamp" in obj
        assert obj["level"] == "INFO"
        assert obj["logger"] == "zsiga.agent.loop"
        assert obj["message"] == "starting"

    def test_structured_context(self):
        """JsonFormatter nests extra attrs under 'context'."""
        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="zsiga.agent.loop",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="tool invocation",
            args=(),
            exc_info=None,
        )
        record.phase = "verify"
        record.tool_name = "bash"
        record.args_preview = "ls -la"
        output = fmt.format(record)
        obj = json.loads(output)
        assert obj["context"]["phase"] == "verify"
        assert obj["context"]["tool_name"] == "bash"
        assert obj["context"]["args_preview"] == "ls -la"

    def test_no_context_when_empty(self):
        """JsonFormatter omits context key when no extra attrs."""
        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        obj = json.loads(output)
        assert "context" not in obj


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------

class TestSetupLogging:
    def test_default_level_info(self):
        """Default setup sets root logger to INFO."""
        setup_logging(LoggingConfig())
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_debug_level(self):
        """setup_logging with level=DEBUG sets root to DEBUG."""
        setup_logging(LoggingConfig(level="DEBUG"))
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_json_formatter(self):
        """setup_logging with fmt=json uses JsonFormatter."""
        setup_logging(LoggingConfig(fmt="json"))
        root = logging.getLogger()
        # Find the console handler
        handlers = [h for h in root.handlers
                    if isinstance(h, logging.StreamHandler)]
        assert any(isinstance(h.formatter, JsonFormatter) for h in handlers)

    def test_text_formatter(self):
        """setup_logging with fmt=text uses TextFormatter."""
        setup_logging(LoggingConfig(fmt="text"))
        root = logging.getLogger()
        handlers = [h for h in root.handlers
                    if isinstance(h, logging.StreamHandler)]
        assert any(isinstance(h.formatter, TextFormatter) for h in handlers)

    def test_file_handler(self):
        """setup_logging creates FileHandler when file is set."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            path = f.name
        try:
            setup_logging(LoggingConfig(file=path))
            root = logging.getLogger()
            file_handlers = [h for h in root.handlers
                             if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
        finally:
            os.unlink(path)

    def test_dual_handler(self):
        """setup_logging creates both StreamHandler and FileHandler."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            path = f.name
        try:
            setup_logging(LoggingConfig(file=path))
            root = logging.getLogger()
            stream_handlers = [h for h in root.handlers
                               if isinstance(h, logging.StreamHandler)
                               and not isinstance(h, logging.FileHandler)]
            file_handlers = [h for h in root.handlers
                             if isinstance(h, logging.FileHandler)]
            assert len(stream_handlers) >= 1
            assert len(file_handlers) == 1
        finally:
            os.unlink(path)

    def test_none_config_defaults(self):
        """setup_logging(None) uses defaults."""
        setup_logging(None)
        root = logging.getLogger()
        assert root.level == logging.INFO


# ---------------------------------------------------------------------------
# LoggingConfig (in zsiga.config)
# ---------------------------------------------------------------------------

class TestLoggingConfig:
    def test_defaults(self):
        from zsiga.config import LoggingConfig as ConfigLoggingConfig
        cfg = ConfigLoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.fmt == "text"
        assert cfg.file is None

    def test_uppercase_level(self):
        from zsiga.config import LoggingConfig as ConfigLoggingConfig
        cfg = ConfigLoggingConfig(level="debug")
        assert cfg.level == "DEBUG"

    def test_json_format(self):
        from zsiga.config import LoggingConfig as ConfigLoggingConfig
        cfg = ConfigLoggingConfig(fmt="json")
        assert cfg.fmt == "json"

    def test_file_path(self):
        from zsiga.config import LoggingConfig as ConfigLoggingConfig
        cfg = ConfigLoggingConfig(file="/var/log/zsiga.log")
        assert cfg.file == "/var/log/zsiga.log"
