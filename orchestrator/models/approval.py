"""
ApprovalRequest — the record this service owns.

LogSentinel's response/policy.py decides an event needs approval
(currently: only "contain"). It POSTs the decision here. This service
does not re-derive severity -> action; it trusts LogSentinel's decision
and owns exactly one thing: who approved or denied it, when, and why.

Event fields below are denormalized copies of what LogSentinel sent,
for display only — this service is not the source of truth for the
event itself, LogSentinel is.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"


class Decision(str, Enum):
    approve = "approve"
    deny = "deny"


class ApprovalCreate(BaseModel):
    """What LogSentinel POSTs when its policy engine flags requires_approval."""

    event_id: str
    action: str  # e.g. "contain"
    policy_reason: str
    detector: str
    rule_id: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_ip: Optional[str] = None
    target: Optional[str] = None
    occurrence_count: int = 1
    correlation_id: Optional[str] = None


class DecisionRequest(BaseModel):
    actor: str = Field(min_length=1)
    decision: Decision
    reason: str = Field(min_length=1)


class ApprovalRequest(ApprovalCreate):
    approval_id: str = Field(default_factory=lambda: f"apr-{uuid4().hex[:12]}")
    status: ApprovalStatus = ApprovalStatus.pending
    created_at: datetime = Field(default_factory=utcnow)

    actor: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_reason: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)
