from fastapi import APIRouter, HTTPException

from orchestrator.models.event import SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS, EventRecord, SecurityEvent
from orchestrator.services import workflow_engine
from orchestrator.storage.repository import Repository

router = APIRouter()
repo = Repository()


@router.post("/events", status_code=201)
def ingest_event(event: SecurityEvent) -> dict:
    if event.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unsupported schema_version '{event.schema_version}'; "
                f"orchestrator supports {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
            ),
        )

    record = EventRecord(**event.model_dump())
    repo.save_event(record)

    workflow = workflow_engine.run(event, repo)
    record.workflow_id = workflow.workflow_id

    return {
        "event_id": record.event_id,
        "workflow_id": workflow.workflow_id,
        "workflow_status": workflow.status,
        "action": workflow.action,
    }


@router.get("/events/{event_id}")
def get_event(event_id: str) -> EventRecord:
    record = repo.get_event(event_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"event {event_id} not found")
    return record


@router.get("/events")
def list_events(limit: int = 50) -> list[EventRecord]:
    return repo.list_events(limit=limit)
