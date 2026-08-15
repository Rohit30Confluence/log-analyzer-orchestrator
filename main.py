from fastapi import FastAPI

from orchestrator.api import events, health, workflows

app = FastAPI(
    title="Analyzer Orchestrator",
    description=(
        "Event routing, policy evaluation, and workflow coordination for "
        "security events produced by analyzer-detection."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(events.router)
app.include_router(workflows.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("orchestrator.main:app", host="0.0.0.0", port=8001, reload=True)
