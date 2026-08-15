from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from orchestrator.api import approvals, health

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="LogSentinel Approval & Audit Service",
    description=(
        "Holds response actions that LogSentinel's policy engine flagged as "
        "requiring human approval (currently: containment), and keeps a "
        "permanent audit record of who approved or denied them, and why."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(approvals.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("orchestrator.main:app", host="0.0.0.0", port=8001, reload=True)
