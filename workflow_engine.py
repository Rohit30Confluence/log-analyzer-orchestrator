"""
Workflow engine — owns state transitions for a Workflow. Nothing outside
this module should mutate Workflow.status directly.
"""
from __future__ import annotations

from datetime import datetime
from orchestrator.util.time import utcnow

from orchestrator.models.event import SecurityEvent
from orchestrator.models.workflow import ALLOWED_TRANSITIONS, Workflow, WorkflowStatus
from orchestrator.services import policy_engine
from orchestrator.storage.repository import Repository


class InvalidTransition(Exception):
    pass


def transition(workflow: Workflow, new_status: WorkflowStatus) -> Workflow:
    current = WorkflowStatus(workflow.status)
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"cannot move workflow from {current} to {new_status}")
    workflow.status = new_status
    workflow.updated_at = utcnow()
    return workflow


def run(event: SecurityEvent, repo: Repository) -> Workflow:
    """
    Create and drive a workflow for a freshly-ingested event through
    evaluation. Stops at awaiting_approval for actions that need a human;
    otherwise marks completed immediately (v0.1 has no real execution
    adapters yet — that's Phase 3/4 work).
    """
    workflow = Workflow(event_id=event.event_id)
    repo.save_workflow(workflow)

    transition(workflow, WorkflowStatus.triggered)
    transition(workflow, WorkflowStatus.evaluating)

    decision = policy_engine.evaluate(event)
    workflow.action = decision.action
    workflow.reason = decision.reason

    if decision.requires_approval:
        transition(workflow, WorkflowStatus.awaiting_approval)
    else:
        # v0.1: no real response adapters wired up yet, so "executing"
        # this action just means recording the decision.
        transition(workflow, WorkflowStatus.completed)

    repo.save_workflow(workflow)
    return workflow


def approve(workflow: Workflow, repo: Repository) -> Workflow:
    transition(workflow, WorkflowStatus.approved)
    transition(workflow, WorkflowStatus.executing)
    transition(workflow, WorkflowStatus.completed)
    repo.save_workflow(workflow)
    return workflow
