"""
Workflow — tracks what the orchestrator decided to do about a SecurityEvent
and what happened when it tried.
"""
from __future__ import annotations

from datetime import datetime
from orchestrator.util.time import utcnow
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(str, Enum):
    created = "created"
    triggered = "triggered"
    evaluating = "evaluating"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    executing = "executing"
    completed = "completed"
    failed = "failed"


class ResponseAction(str, Enum):
    observe = "observe"
    record = "record"
    notify = "notify"
    contain = "contain"


# Legal transitions. Anything not listed here is rejected by the engine.
ALLOWED_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.created: {WorkflowStatus.triggered},
    WorkflowStatus.triggered: {WorkflowStatus.evaluating},
    WorkflowStatus.evaluating: {
        WorkflowStatus.awaiting_approval,
        WorkflowStatus.executing,
        WorkflowStatus.completed,
    },
    WorkflowStatus.awaiting_approval: {
        WorkflowStatus.approved,
        WorkflowStatus.failed,
    },
    WorkflowStatus.approved: {WorkflowStatus.executing},
    WorkflowStatus.executing: {WorkflowStatus.completed, WorkflowStatus.failed},
    WorkflowStatus.completed: set(),
    WorkflowStatus.failed: set(),
}


class Workflow(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid4().hex[:12]}")
    event_id: str
    status: WorkflowStatus = WorkflowStatus.created
    action: Optional[ResponseAction] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(use_enum_values=True)
