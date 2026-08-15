"""
approval_client.py — LogSentinel-side client for logsentinel-audit-service.

Fails closed: if the audit service is unreachable, treat the event as
NOT approved rather than executing anyway.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx

APPROVAL_SERVICE_URL = os.environ.get("APPROVAL_SERVICE_URL", "http://localhost:8002")
TIMEOUT_SECONDS = 3.0


def request_approval(event: Dict[str, Any], decision: Any) -> bool:
    """
    POST a pending approval to the audit service. Call this at the same
    point response/policy.py returns requires_approval=True — before
    execute() is ever invoked for that event.

    Returns True if recorded, False if the service was unreachable
    (LogSentinel's own event.status stays the fallback source of truth).
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
    """Fails closed: any error (network, service down) returns False."""
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
