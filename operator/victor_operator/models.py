from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class Action(BaseModel):
    tool: str = Field(min_length=1, max_length=80)
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="", max_length=1000)


class FinishAction(BaseModel):
    tool: Literal["finish"] = "finish"
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="Task success conditions are satisfied.")


class ToolResult(BaseModel):
    ok: bool
    output: Any = None
    error: str | None = None
    evidence: list[str] = Field(default_factory=list)
    duration_ms: int = 0


class HistoryEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    kind: str
    action: Action | None = None
    result: ToolResult | None = None
    message: str = ""


class TaskCreate(BaseModel):
    goal: str = Field(min_length=3, max_length=12000)
    success_conditions: list[str] = Field(default_factory=list, max_length=30)
    steps: list[Action] | None = None
    max_steps: int | None = Field(default=None, ge=1, le=200)


class TaskRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    goal: str
    success_conditions: list[str] = Field(default_factory=list)
    explicit_steps: list[Action] | None = None
    status: TaskStatus = TaskStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    max_steps: int = 40
    step_count: int = 0
    history: list[HistoryEvent] = Field(default_factory=list)
    pending_action: Action | None = None
    approved_action_digest: str | None = None
    summary: str | None = None
    error: str | None = None


class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool = False
    risk: RiskLevel = RiskLevel.LOW
    reason: str = ""


class ApprovalRequest(BaseModel):
    approve: bool
    note: str = Field(default="", max_length=1000)
