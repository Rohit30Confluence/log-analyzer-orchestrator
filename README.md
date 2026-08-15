# Analyzer Orchestrator

> Event routing, policy evaluation, and workflow coordination for security
> events produced by [analyzer-detection](https://github.com/Rohit30Confluence/log-analyzer-attack-detection).

## What this is

Detection answers **"what happened?"** Orchestrator answers **"what should
happen because of it?"**

```
SecurityEvent
     │
     ▼
POST /events
     │
     ├── validate schema
     ├── persist
     ├── evaluate policy (severity + confidence → action)
     └── drive workflow state machine
              │
              ▼
     observe / record / notify / contain
     (contain requires explicit approval)
```

This is **not** a deployment/CI/DNS automation tool. An earlier version of
this README described that scope; it wasn't built and doesn't reflect what
this repo does. If deployment/service-health coordination gets built later,
it'll be a genuinely separate capability layered on top of this — not the
other way around.

## Architecture

- **FastAPI** service, **SQLite** persistence (no external deps to run)
- `orchestrator/models/event.py` — the `SecurityEvent` schema contract with
  the detection repo. **This is the seam between the two repos.** If you
  change a field here, mirror it on the detection side and bump
  `schema_version`.
- `orchestrator/services/policy_engine.py` — severity/confidence → response
  action
- `orchestrator/services/workflow_engine.py` — state machine
  (`created → triggered → evaluating → [awaiting_approval] → executing → completed/failed`)
- `orchestrator/storage/repository.py` — SQLite, swappable later

## Policy (v0.1)

| Severity | Action    | Requires approval |
|----------|-----------|--------------------|
| low      | observe   | no                 |
| medium   | record    | no                 |
| high     | notify    | no                 |
| critical | contain   | **yes**            |

Confidence below `0.5` downgrades any non-`observe` action to `record` —
an unsure detection shouldn't trigger an aggressive response.

## Usage

```bash
pip install -r requirements.txt
uvicorn orchestrator.main:app --reload --port 8001
```

```bash
curl -X POST http://localhost:8001/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "security_detection",
    "detector": {"name": "web.sql_injection", "rule_id": "SQLI-001"},
    "severity": "critical",
    "confidence": 0.94,
    "source": {"ip": "10.0.0.25"},
    "target": {"path": "/login", "method": "POST"},
    "observed_at": "2026-08-15T09:20:31Z",
    "correlation_id": "corr-abc"
  }'
```

Endpoints:

- `POST /events` — ingest a `SecurityEvent`, returns the resulting workflow
- `GET /events/{event_id}` / `GET /events`
- `GET /workflows/{workflow_id}`
- `POST /workflows/{workflow_id}/approve` — approve a `contain` action stuck
  at `awaiting_approval`
- `GET /health`

## Testing

```bash
pytest tests/ -v
```

14 tests: event ingestion/validation, policy decisions across all severity
tiers, and workflow state-machine legality (including that terminal states
have no outgoing transitions).

## Docker

```bash
docker build -t analyzer-orchestrator .
docker run -p 8001:8001 analyzer-orchestrator
```

## Roadmap

- [x] Phase 1 — event ingestion, schema validation, SQLite persistence
- [x] Phase 2 — policy engine
- [x] Phase 3 — workflow state machine + approval gate
- [ ] Phase 3.5 — wire `analyzer-detection` to actually POST events here
      (currently the schema matches; no live integration yet)
- [ ] Phase 4 — response execution adapters (notify/contain actually *do*
      something instead of just recording a decision)
- [ ] Phase 4 — service health monitoring (this is where deployment/DNS
      concerns belong, if we build them — as a supporting capability, not
      the project's purpose)

## Relationship to analyzer-detection

Both repos share the `SecurityEvent` schema
(`orchestrator/models/event.py` here). Detection produces events;
orchestrator consumes them. Orchestrator does not re-implement detection
logic — if you find yourself adding pattern-matching or scoring here,
that belongs in the detection repo instead.

Maintainer: @Rohit30Confluence
License: MIT
