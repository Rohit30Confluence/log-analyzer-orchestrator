from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from orchestrator.dependencies import get_repository
from orchestrator.models.approval import (
    ApprovalCreate,
    ApprovalRequest,
    ApprovalStatus,
    Decision,
    DecisionRequest,
)
from orchestrator.models.approval import utcnow
from orchestrator.storage.repository import Repository

router = APIRouter()


@router.post("/approvals", status_code=201)
def create_approval(
    payload: ApprovalCreate, repo: Repository = Depends(get_repository)
) -> ApprovalRequest:
    """
    Called by LogSentinel when its policy engine flags requires_approval.
    We don't re-check the policy decision here — LogSentinel already made
    it. We only open a pending record for a human to act on.
    """
    approval = ApprovalRequest(**payload.model_dump())
    repo.save(approval)
    return approval


@router.get("/approvals")
def list_approvals(
    status: Optional[ApprovalStatus] = Query(default=None),
    limit: int = Query(default=100, le=500),
    repo: Repository = Depends(get_repository),
) -> list[ApprovalRequest]:
    return repo.list(status=status, limit=limit)


@router.get("/approvals/{approval_id}")
def get_approval(
    approval_id: str, repo: Repository = Depends(get_repository)
) -> ApprovalRequest:
    approval = repo.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"approval {approval_id} not found")
    return approval


@router.post("/approvals/{approval_id}/decide")
def decide_approval(
    approval_id: str,
    payload: DecisionRequest,
    repo: Repository = Depends(get_repository),
) -> ApprovalRequest:
    approval = repo.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"approval {approval_id} not found")

    if ApprovalStatus(approval.status) != ApprovalStatus.pending:
        # Idempotency guard: a decided approval cannot be re-decided,
        # not even to the same outcome. Prevents double-click races from
        # silently overwriting an audit record.
        raise HTTPException(
            status_code=409,
            detail=f"approval {approval_id} is already '{approval.status}', cannot re-decide",
        )

    approval.status = (
        ApprovalStatus.approved.value if payload.decision == Decision.approve else ApprovalStatus.denied.value
    )
    approval.actor = payload.actor
    approval.decision_reason = payload.reason
    approval.decided_at = utcnow()

    repo.save(approval)
    return approval
