"""Log JSON ra stderr. stdout dành riêng cho giao thức MCP stdio."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, TextIO
from zoneinfo import ZoneInfo

from mcp_server.errors import redact

_HANDLER_NAME = "taskmate-json"
LOG_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class JsonFormatter(logging.Formatter):
    """Mỗi bản ghi một dòng JSON. Mọi bí mật đã biết được thay bằng '***'."""

    def __init__(self, secrets: list[str] | None = None) -> None:
        super().__init__()
        self._secrets = [s for s in (secrets or []) if s]

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, LOG_TZ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        data = getattr(record, "data", None)
        if isinstance(data, dict):
            entry.update(data)
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return redact(json.dumps(entry, ensure_ascii=False, default=str), self._secrets)


def configure_logging(
    secrets: list[str] | None = None, level: int = logging.INFO, stream: TextIO | None = None
) -> logging.Handler:
    """Gắn handler JSON vào root logger (thay handler cũ nếu đã gắn). Mặc định ghi ra stderr."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if handler.get_name() == _HANDLER_NAME:
            root.removeHandler(handler)
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(JsonFormatter(secrets))
    root.addHandler(handler)
    root.setLevel(level)
    return handler
