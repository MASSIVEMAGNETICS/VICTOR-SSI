from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from .models import TaskRecord, TaskStatus


class TaskStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def save(self, task: TaskRecord) -> TaskRecord:
        task.updated_at = datetime.now(UTC)
        payload = task.model_dump_json()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO tasks(id, status, created_at, updated_at, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    payload=excluded.payload
                """,
                (
                    task.id,
                    task.status.value,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    payload,
                ),
            )
            self._connection.commit()
        return task

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return TaskRecord.model_validate_json(row["payload"]) if row else None

    def list(self, limit: int = 100) -> list[TaskRecord]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT payload FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [TaskRecord.model_validate_json(row["payload"]) for row in rows]

    def claim_next(self) -> TaskRecord | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload FROM tasks WHERE status = ? ORDER BY created_at LIMIT 1",
                (TaskStatus.QUEUED.value,),
            ).fetchone()
            if not row:
                return None
            task = TaskRecord.model_validate_json(row["payload"])
            task.status = TaskStatus.RUNNING
            self.save(task)
            return task

    def export_jsonl(self, destination: Path) -> None:
        with destination.open("w", encoding="utf-8") as handle:
            for task in reversed(self.list(limit=100000)):
                handle.write(json.dumps(task.model_dump(mode="json"), ensure_ascii=False) + "\n")
