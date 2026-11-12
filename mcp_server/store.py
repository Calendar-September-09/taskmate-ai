"""Lưu trạng thái của MCP Server trong SQLite: mã approval đã dùng và issue đã tạo."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

_SCHEMA = """
CREATE TABLE IF NOT EXISTS used_approvals (
    jti TEXT PRIMARY KEY,
    approver TEXT NOT NULL,
    used_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS created_issues (
    draft_hash TEXT PRIMARY KEY,
    issue_key TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class CreatedRecord(BaseModel):
    draft_hash: str
    issue_key: str
    url: str


class ServerStore:
    def __init__(self, db_path: Path | str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as conn, conn:
            yield conn

    def consume_approval(self, jti: str, approver: str, now: datetime) -> bool:
        """Đánh dấu mã đã dùng. Trả False nếu mã đã được dùng trước đó."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO used_approvals (jti, approver, used_at) VALUES (?, ?, ?)",
                    (jti, approver, now.isoformat()),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def get_created(self, draft_hash: str) -> CreatedRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT draft_hash, issue_key, url FROM created_issues WHERE draft_hash = ?",
                (draft_hash,),
            ).fetchone()
        if row is None:
            return None
        return CreatedRecord(draft_hash=row[0], issue_key=row[1], url=row[2])

    def save_created(self, draft_hash: str, issue_key: str, url: str, now: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO created_issues (draft_hash, issue_key, url, created_at) "
                "VALUES (?, ?, ?, ?)",
                (draft_hash, issue_key, url, now.isoformat()),
            )

    def forget_created(self, draft_hash: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM created_issues WHERE draft_hash = ?", (draft_hash,))
