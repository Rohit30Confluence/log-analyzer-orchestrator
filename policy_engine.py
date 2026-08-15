"""
Policy engine — decides WHAT SHOULD HAPPEN given a SecurityEvent.

This is deliberately separate from detection's confidence scoring.
Detection decides "how sure am I this is an attack." Policy decides
"given that, what's the appropriate response." Keeping these separate
is the whole point of the two-repo split — don't collapse them.
"""
from __future__ import annotations

from orchestrator.models.event import SecurityEvent, Severity
from orchestrator.models.workflow import ResponseAction

# Confidence threshold below which we downgrade the response by one tier,
# regardless of severity — an unsure detector shouldn't trigger containment.
LOW_CONFIDENCE_THRESHOLD = 0.5

_BASE_POLICY: dict[Severity, ResponseAction] = {
    Severity.low: ResponseAction.observe,
    Severity.medium: ResponseAction.record,
    Severity.high: ResponseAction.notify,
    Severity.critical: ResponseAction.contain,
}

_REQUIRES_APPROVAL = {ResponseAction.contain}


class PolicyDecision:
    def __init__(self, action: ResponseAction, requires_approval: bool, reason: str):
        self.action = action
        self.requires_approval = requires_approval
        self.reason = reason


def evaluate(event: SecurityEvent) -> PolicyDecision:
    severity = Severity(event.severity)
    action = _BASE_POLICY[severity]
    reason = f"severity={severity.value} -> {action.value}"

    if event.confidence < LOW_CONFIDENCE_THRESHOLD and action != ResponseAction.observe:
        # Downgrade: low confidence means don't act aggressively on it.
        action = ResponseAction.record if action != ResponseAction.observe else action
        reason += f"; downgraded, confidence={event.confidence} < {LOW_CONFIDENCE_THRESHOLD}"

    requires_approval = action in _REQUIRES_APPROVAL

    return PolicyDecision(action=action, requires_approval=requires_approval, reason=reason)
