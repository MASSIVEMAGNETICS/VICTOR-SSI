from pathlib import Path

import pytest

from victor_operator.config import Settings
from victor_operator.executors import ExecutorHub
from victor_operator.models import Action, TaskRecord, TaskStatus
from victor_operator.planner import Planner
from victor_operator.policy import PolicyEngine
from victor_operator.store import TaskStore
from victor_operator.worker import Worker


def make_worker(tmp_path: Path) -> tuple[Settings, TaskStore, Worker]:
    settings = Settings(
        VICTOR_API_TOKEN="x" * 32,
        VICTOR_WORKSPACE=tmp_path / "workspace",
        VICTOR_DATA_DIR=tmp_path / "data",
    )
    settings.prepare()
    store = TaskStore(settings.data_dir / "test.sqlite3")
    policy = PolicyEngine(settings)
    worker = Worker(
        store,
        Planner(settings),
        policy,
        ExecutorHub(settings, policy),
    )
    return settings, store, worker


@pytest.mark.asyncio
async def test_explicit_file_plan_completes(tmp_path: Path) -> None:
    settings, store, worker = make_worker(tmp_path)
    task = TaskRecord(
        goal="Create hello.txt",
        explicit_steps=[
            Action(
                tool="filesystem.write",
                arguments={"path": "hello.txt", "content": "hello"},
            )
        ],
    )
    store.save(task)
    claimed = store.claim_next()
    assert claimed is not None
    await worker._run_task(claimed)
    finished = store.get(task.id)
    assert finished is not None
    assert finished.status == TaskStatus.COMPLETED
    assert (settings.workspace / "hello.txt").read_text(encoding="utf-8") == "hello"


@pytest.mark.asyncio
async def test_goal_without_explicit_plan_fails_closed_even_with_cloud_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A stray legacy/cloud credential must never reactivate hosted cognition.
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    _settings, store, worker = make_worker(tmp_path)
    task = TaskRecord(goal="Inspect the workspace and decide what to do next.")
    store.save(task)

    claimed = store.claim_next()
    assert claimed is not None
    await worker._run_task(claimed)

    finished = store.get(task.id)
    assert finished is not None
    assert finished.status == TaskStatus.FAILED
    assert finished.step_count == 0
    assert finished.error is not None
    assert "VICTOR_MODEL_SOVEREIGNTY" in finished.error
    assert "explicit `steps` plan" in finished.error
