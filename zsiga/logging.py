"""Structured logging infrastructure for zsiga.

Provides TextFormatter (human-readable, preserves visual style) and
JsonFormatter (one JSON object per line), plus setup_logging() that
reads a LoggingConfig to configure the root logger.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class LoggingConfig:
    """Logging configuration parsed from the ``logging`` section of zsiga.yaml.

    All fields are optional and default to sensible values.
    """

    def __init__(
        self,
        level: str = "INFO",
        fmt: str = "text",
        file: str | None = None,
    ):
        self.level = level.upper()
        self.fmt = fmt
        self.file = file


class TextFormatter(logging.Formatter):
    """Human-readable formatter that preserves the visual style of print().

    When the log record carries a ``phase`` key in its *extra* dict, the
    output line is formatted as ``  [phase] message`` to match the previous
    ``print(f"  [{phase}] ...")`` calls.  For records without a phase the
    plain message is emitted.
    """

    def format(self, record: logging.LogRecord) -> str:
        phase = getattr(record, "phase", None)
        message = record.getMessage()

        if phase:
            return f"  [{phase}] {message}"
        return message


class JsonFormatter(logging.Formatter):
    """Machine-readable formatter producing one JSON object per line.

    Output schema::

        {
          "timestamp": "2024-01-15T10:30:00.123456+00:00",
          "level": "INFO",
          "logger": "zsiga.agent.loop",
          "message": "...",
          "context": { ... }
        }

    Any structured context passed via ``extra`` (phase, turn, tool_name,
    etc.) is collected under the ``context`` key.
    """

    # Attributes that are part of the standard LogRecord and should NOT
    # be included in the context dict.
    _RESERVED = frozenset({
        "name", "msg", "args", "created", "relativeCreated",
        "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "pathname", "filename", "module", "levelno", "levelname",
        "thread", "threadName", "process", "processName", "msecs",
        "message", "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).isoformat()

        context: dict = {}
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in self._RESERVED:
                continue
            context[key] = value

        obj: dict = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if context:
            obj["context"] = context

        # Append exception info if present
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            obj["exception"] = record.exc_text

        return json.dumps(obj, ensure_ascii=False, default=str)


def setup_logging(config: LoggingConfig | None = None) -> None:
    """Configure the root logger based on *config*.

    This function should be called once at application startup, before
    any log messages are emitted.

    Parameters
    ----------
    config:
        A :class:`LoggingConfig` instance.  If ``None``, defaults are used
        (level=INFO, format=text, output=stderr).
    """
    if config is None:
        config = LoggingConfig()

    root = logging.getLogger()
    root.setLevel(config.level)

    # Remove any existing handlers to avoid duplicates on repeated calls
    root.handlers.clear()

    # Choose formatter
    if config.fmt == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = TextFormatter()

    # Console handler (stderr)
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Optional file handler (dual output)
    if config.file:
        file_handler = logging.FileHandler(config.file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
