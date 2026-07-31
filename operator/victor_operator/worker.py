from __future__ import annotations

import asyncio

from .executors import ExecutorHub
from .models import Action, HistoryEvent, TaskRecord, TaskStatus
from .planner import Planner, PlannerError
from .policy import PolicyEngine, action_digest
from .store import TaskStore


class Worker:
    def __init__(
        self,
        store: TaskStore,
        planner: Planner,
        policy: PolicyEngine,
        executors: ExecutorHub,
    ):
        self.store = store
        self.planner = planner
        self.policy = policy
        self.executors = executors
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    async def run_forever(self) -> None:
        while not self._stop.is_set():
            task = self.store.claim_next()
            if task is None:
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=0.5)
                except TimeoutError:
                    pass
                continue
            await self._run_task(task)

    async def _run_task(self, task: TaskRecord) -> None:
        while task.status == TaskStatus.RUNNING:
            fresh = self.store.get(task.id)
            if fresh is None:
                return
            task = fresh
            if task.status == TaskStatus.CANCELLED:
                return
            if task.step_count >= task.max_steps:
                task.status = TaskStatus.FAILED
                task.error = f"Maximum step limit reached ({task.max_steps})."
                self.store.save(task)
                return

            try:
                action = self._resolve_action(task)
            except PlannerError as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                self.store.save(task)
                return

            if action.tool == "finish":
                task.status = TaskStatus.COMPLETED
                task.summary = str(action.arguments.get("summary", "Task completed."))
                task.history.append(
                    HistoryEvent(kind="finished", action=action, message=task.summary)
                )
                self.store.save(task)
                return

            decision = self.policy.evaluate(action)
            task.history.append(
                HistoryEvent(
                    kind="policy",
                    action=action,
                    message=f"{decision.risk}: {decision.reason}",
                )
            )
            if not decision.allowed:
                task.status = TaskStatus.FAILED
                task.error = decision.reason
                self.store.save(task)
                return

            digest = action_digest(action)
            if decision.requires_approval and task.approved_action_digest != digest:
                task.pending_action = action
                task.status = TaskStatus.WAITING_APPROVAL
                task.history.append(
                    HistoryEvent(
                        kind="approval_required", action=action, message=decision.reason
                    )
                )
                self.store.save(task)
                return

            task.pending_action = None
            task.approved_action_digest = None
            result = await self.executors.execute(action)
            task.step_count += 1
            task.history.append(HistoryEvent(kind="tool_result", action=action, result=result))
            if not result.ok and task.explicit_steps is not None:
                task.status = TaskStatus.FAILED
                task.error = result.error or "Explicit step failed."
            self.store.save(task)

    def _resolve_action(self, task: TaskRecord) -> Action:
        if (
            task.pending_action is not None
            and task.approved_action_digest == action_digest(task.pending_action)
        ):
            return task.pending_action
        return self.planner.next_action(task)
