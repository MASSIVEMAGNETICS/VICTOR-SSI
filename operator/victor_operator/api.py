from __future__ import annotations

import asyncio
import hmac
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from .config import Settings
from .executors import ExecutorHub
from .models import ApprovalRequest, HistoryEvent, TaskCreate, TaskRecord, TaskStatus
from .planner import Planner
from .policy import PolicyEngine, action_digest
from .store import TaskStore
from .worker import Worker


DASHBOARD = """<!doctype html><html><head><meta charset='utf-8'><title>Victor Operator</title>
<style>body{font:16px system-ui;max-width:920px;margin:40px auto;padding:0 16px;background:#101114;color:#eee}textarea,input{width:100%;box-sizing:border-box;background:#191b20;color:#eee;border:1px solid #444;padding:12px}button{padding:10px 16px;margin:8px 8px 8px 0}pre{white-space:pre-wrap;background:#191b20;padding:12px;overflow:auto}.task{border:1px solid #333;padding:16px;margin:14px 0}</style></head>
<body><h1>Victor Operator</h1><p>Local-first digital employee control plane.</p><label>API token</label><input id='token' type='password'><label>Goal</label><textarea id='goal' rows='6'></textarea><button onclick='submitTask()'>Execute</button><button onclick='loadTasks()'>Refresh</button><div id='tasks'></div>
<script>const headers=()=>({'Content-Type':'application/json','Authorization':'Bearer '+document.querySelector('#token').value});async function submitTask(){let r=await fetch('/v1/tasks',{method:'POST',headers:headers(),body:JSON.stringify({goal:document.querySelector('#goal').value})});alert(r.ok?'Queued':await r.text());loadTasks()}async function approve(id,yes){await fetch('/v1/tasks/'+id+'/approval',{method:'POST',headers:headers(),body:JSON.stringify({approve:yes})});loadTasks()}async function loadTasks(){let r=await fetch('/v1/tasks',{headers:headers()});if(!r.ok){document.querySelector('#tasks').innerText=await r.text();return}let rows=await r.json();document.querySelector('#tasks').innerHTML=rows.map(t=>`<div class=task><b>${t.status}</b> — ${t.goal}<pre>${JSON.stringify(t.history.slice(-4),null,2)}</pre>${t.status==='waiting_approval'?`<button onclick=\"approve('${t.id}',true)\">Approve once</button><button onclick=\"approve('${t.id}',false)\">Reject</button>`:''}</div>`).join('')}</script></body></html>"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.prepare()
    store = TaskStore(settings.data_dir / "operator.sqlite3")
    policy = PolicyEngine(settings)
    planner = Planner(settings)
    executors = ExecutorHub(settings, policy)
    worker = Worker(store, planner, policy, executors)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        worker_task = asyncio.create_task(
            worker.run_forever(), name="victor-operator-worker"
        )
        yield
        worker.stop()
        await worker_task
        await executors.close()

    app = FastAPI(title="Victor Operator", version="0.1.0", lifespan=lifespan)

    def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
        expected = f"Bearer {settings.api_token}"
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token"
            )

    @app.get("/", response_class=HTMLResponse)
    async def dashboard() -> str:
        return DASHBOARD

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "victor-operator",
            "workspace": str(settings.workspace),
        }

    @app.post(
        "/v1/tasks", response_model=TaskRecord, dependencies=[Depends(require_token)]
    )
    async def create_task(request: TaskCreate) -> TaskRecord:
        task = TaskRecord(
            goal=request.goal,
            success_conditions=request.success_conditions,
            explicit_steps=request.steps,
            max_steps=request.max_steps or settings.max_steps,
        )
        return store.save(task)

    @app.get(
        "/v1/tasks",
        response_model=list[TaskRecord],
        dependencies=[Depends(require_token)],
    )
    async def list_tasks(
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> list[TaskRecord]:
        return store.list(limit)

    @app.get(
        "/v1/tasks/{task_id}",
        response_model=TaskRecord,
        dependencies=[Depends(require_token)],
    )
    async def get_task(task_id: str) -> TaskRecord:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.post(
        "/v1/tasks/{task_id}/approval",
        response_model=TaskRecord,
        dependencies=[Depends(require_token)],
    )
    async def decide_approval(task_id: str, request: ApprovalRequest) -> TaskRecord:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status != TaskStatus.WAITING_APPROVAL or task.pending_action is None:
            raise HTTPException(status_code=409, detail="Task is not waiting for approval")
        if request.approve:
            task.approved_action_digest = action_digest(task.pending_action)
            task.status = TaskStatus.QUEUED
            task.history.append(
                HistoryEvent(
                    kind="approved", action=task.pending_action, message=request.note
                )
            )
        else:
            task.status = TaskStatus.FAILED
            task.error = request.note or "Operator rejected the pending action."
            task.history.append(
                HistoryEvent(
                    kind="rejected", action=task.pending_action, message=task.error
                )
            )
        return store.save(task)

    @app.post(
        "/v1/tasks/{task_id}/cancel",
        response_model=TaskRecord,
        dependencies=[Depends(require_token)],
    )
    async def cancel_task(task_id: str) -> TaskRecord:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }:
            raise HTTPException(status_code=409, detail="Task is already terminal")
        task.status = TaskStatus.CANCELLED
        task.history.append(
            HistoryEvent(kind="cancelled", message="Cancelled by operator.")
        )
        return store.save(task)

    return app
