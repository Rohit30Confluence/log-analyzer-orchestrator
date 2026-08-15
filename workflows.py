from fastapi import APIRouter, HTTPException

from orchestrator.models.workflow import Workflow, WorkflowStatus
from orchestrator.services import workflow_engine
from orchestrator.storage.repository import Repository

router = APIRouter()
repo = Repository()


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str) -> Workflow:
    workflow = repo.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"workflow {workflow_id} not found")
    return workflow


@router.post("/workflows/{workflow_id}/approve")
def approve_workflow(workflow_id: str) -> Workflow:
    workflow = repo.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"workflow {workflow_id} not found")
    if WorkflowStatus(workflow.status) != WorkflowStatus.awaiting_approval:
        raise HTTPException(
            status_code=409,
            detail=f"workflow {workflow_id} is '{workflow.status}', not awaiting_approval",
        )
    return workflow_engine.approve(workflow, repo)
