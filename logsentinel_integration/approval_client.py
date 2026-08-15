"""
approval_client.py — drop this into LogSentinel's backend/app/response/.

Call this from executor.py right before executing a "contain" action.
Fails closed: if the approval service is unreachable, treat the event
as NOT approved rather than executing anyway.

Usage in executor.py:

    from .approval_client import request_approval, check_approval

    # when policy.evaluate_event() returns requires_approval=True:
    request_approval(event, decision)

    # in ResponseExecutor.execute(), before executing "contain":
    if requires_approval and not check_approval(event_id):
        return ExecutionResult(status="pending_approval", ...)
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx

APPROVAL_SERVICE_URL = os.environ.get("APPROVAL_SERVICE_URL", "http://localhost:8002")
TIMEOUT_SECONDS = 3.0


def request_approval(event: Dict[str, Any], decision: Any) -> bool:
    """
    POST a pending approval to the approval service. Returns True if the
    request was recorded, False if the service was unreachable (caller
    should treat this as "still pending" — LogSentinel keeps its own
    lifecycle status as the fallback source of truth).
    """
    payload = {
        "event_id": event["event_id"],
        "action": decision.action,
        "policy_reason": decision.reason,
        "detector": event["detector"],
        "rule_id": event["rule_id"],
        "severity": event["severity"],
        "confidence": event["confidence"],
        "source_ip": event.get("source_ip"),
        "target": event.get("target"),
        "occurrence_count": event.get("occurrence_count", 1),
        "correlation_id": event.get("correlation_id"),
    }
    try:
        resp = httpx.post(
            f"{APPROVAL_SERVICE_URL}/approvals", json=payload, timeout=TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        return True
    except httpx.HTTPError:
        return False


def check_approval(event_id: str) -> bool:
    """
    Look up whether this event's approval has been granted.
    Fails closed: any error (network, 404, service down) returns False.
    """
    try:
        resp = httpx.get(
            f"{APPROVAL_SERVICE_URL}/approvals",
            params={"status": "approved"},
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        approved = resp.json()
        return any(a["event_id"] == event_id for a in approved)
    except httpx.HTTPError:
        return False
