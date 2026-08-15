import pytest
from fastapi.testclient import TestClient

from orchestrator import main
from orchestrator.dependencies import set_repository
from orchestrator.storage.repository import Repository


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    set_repository(Repository(db_path))
    return TestClient(main.app)


def make_approval(**overrides) -> dict:
    base = {
        "event_id": "evt-abc123",
        "action": "contain",
        "policy_reason": "critical event has high confidence and repeated occurrences",
        "detector": "web.sql_injection",
        "rule_id": "SQLI-001",
        "severity": "critical",
        "confidence": 0.95,
        "source_ip": "10.0.0.25",
        "target": "/login",
        "occurrence_count": 3,
        "correlation_id": None,
    }
    base.update(overrides)
    return base
