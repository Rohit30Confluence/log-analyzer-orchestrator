from orchestrator.util.time import utcnow

from orchestrator.models.event import Detector, SecurityEvent
from orchestrator.models.workflow import ResponseAction
from orchestrator.services import policy_engine


def _event(severity: str, confidence: float) -> SecurityEvent:
    return SecurityEvent(
        event_type="security_detection",
        detector=Detector(name="web.sql_injection", rule_id="SQLI-001"),
        severity=severity,
        confidence=confidence,
        observed_at=utcnow(),
    )


def test_low_severity_maps_to_observe():
    decision = policy_engine.evaluate(_event("low", 0.9))
    assert decision.action == ResponseAction.observe
    assert decision.requires_approval is False


def test_critical_severity_maps_to_contain_and_requires_approval():
    decision = policy_engine.evaluate(_event("critical", 0.95))
    assert decision.action == ResponseAction.contain
    assert decision.requires_approval is True


def test_low_confidence_downgrades_high_severity():
    decision = policy_engine.evaluate(_event("high", 0.2))
    assert decision.action == ResponseAction.record
    assert "downgraded" in decision.reason
