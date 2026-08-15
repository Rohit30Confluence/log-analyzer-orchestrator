"""
SecurityEvent — the shared contract between analyzer-detection and
analyzer-orchestrator.

Detection PRODUCES this. Orchestrator CONSUMES this. If you change a field
here, you must change it in the detection repo's equivalent model too, and
bump SCHEMA_VERSION. The orchestrator rejects events whose schema_version
it doesn't recognize rather than guessing at a shape.
"""
from __future__ import annotations

from datetime import datetime
from orchestrator.util.time import utcnow
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Detector(BaseModel):
    name: str  # e.g. "web.sql_injection"
    rule_id: str  # e.g. "SQLI-001"


class Source(BaseModel):
    ip: Optional[str] = None


class Target(BaseModel):
    path: Optional[str] = None
    method: Optional[str] = None


class Evidence(BaseModel):
    pattern: Optional[str] = None
    request: Optional[str] = None


class SecurityEvent(BaseModel):
    schema_version: str = Field(default=SCHEMA_VERSION)
    event_id: str = Field(default_factory=lambda: f"evt-{uuid4().hex[:12]}")
    event_type: str  # e.g. "security_detection"
    detector: Detector
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    source: Source = Field(default_factory=Source)
    target: Target = Field(default_factory=Target)
    observed_at: datetime
    correlation_id: Optional[str] = None
    evidence: Optional[Evidence] = None

    model_config = ConfigDict(use_enum_values=True)


class EventRecord(SecurityEvent):
    """SecurityEvent as persisted, with orchestrator-assigned bookkeeping."""

    received_at: datetime = Field(default_factory=utcnow)
    workflow_id: Optional[str] = None
