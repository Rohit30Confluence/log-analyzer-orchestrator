from tests.conftest import make_approval


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_dashboard_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_create_approval_returns_pending(client):
    resp = client.post("/approvals", json=make_approval())
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["approval_id"].startswith("apr-")
    assert body["actor"] is None


def test_get_approval_by_id(client):
    created = client.post("/approvals", json=make_approval()).json()
    resp = client.get(f"/approvals/{created['approval_id']}")
    assert resp.status_code == 200
    assert resp.json()["approval_id"] == created["approval_id"]


def test_get_missing_approval_404s(client):
    resp = client.get("/approvals/apr-doesnotexist")
    assert resp.status_code == 404


def test_list_filters_by_status(client):
    client.post("/approvals", json=make_approval())
    a2 = client.post("/approvals", json=make_approval(event_id="evt-2")).json()
    client.post(
        f"/approvals/{a2['approval_id']}/decide",
        json={"actor": "rohit", "decision": "approve", "reason": "confirmed campaign"},
    )

    pending = client.get("/approvals?status=pending").json()
    approved = client.get("/approvals?status=approved").json()
    assert len(pending) == 1
    assert len(approved) == 1
    assert approved[0]["event_id"] == "evt-2"


def test_approve_records_actor_and_reason(client):
    created = client.post("/approvals", json=make_approval()).json()
    resp = client.post(
        f"/approvals/{created['approval_id']}/decide",
        json={"actor": "rohit", "decision": "approve", "reason": "verified attack pattern"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["actor"] == "rohit"
    assert body["decision_reason"] == "verified attack pattern"
    assert body["decided_at"] is not None


def test_deny_records_correctly(client):
    created = client.post("/approvals", json=make_approval()).json()
    resp = client.post(
        f"/approvals/{created['approval_id']}/decide",
        json={"actor": "rohit", "decision": "deny", "reason": "false positive, known scanner"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "denied"


def test_cannot_redecide_already_decided_approval(client):
    created = client.post("/approvals", json=make_approval()).json()
    client.post(
        f"/approvals/{created['approval_id']}/decide",
        json={"actor": "rohit", "decision": "approve", "reason": "first decision"},
    )
    resp = client.post(
        f"/approvals/{created['approval_id']}/decide",
        json={"actor": "someone-else", "decision": "deny", "reason": "trying to override"},
    )
    assert resp.status_code == 409
    # original decision must be untouched
    unchanged = client.get(f"/approvals/{created['approval_id']}").json()
    assert unchanged["status"] == "approved"
    assert unchanged["actor"] == "rohit"


def test_decide_missing_approval_404s(client):
    resp = client.post(
        "/approvals/apr-doesnotexist/decide",
        json={"actor": "rohit", "decision": "approve", "reason": "x"},
    )
    assert resp.status_code == 404


def test_decide_requires_actor_and_reason(client):
    created = client.post("/approvals", json=make_approval()).json()
    resp = client.post(
        f"/approvals/{created['approval_id']}/decide",
        json={"actor": "", "decision": "approve", "reason": ""},
    )
    assert resp.status_code == 422


def test_confidence_out_of_range_rejected(client):
    resp = client.post("/approvals", json=make_approval(confidence=1.5))
    assert resp.status_code == 422
