# LogSentinel Approval & Audit Service

> The one piece LogSentinel's response layer doesn't have: a record of
> *who* approved a containment action, *when*, and *why* — kept in a
> separate service on purpose, so detection can't also be the thing that
> grants itself permission to act.

## Why this exists (and why it's small)

[LogSentinel](https://github.com/Rohit30Confluence/log-analyzer-attack-detection)
already does detection, policy decision, and dry-run response execution
in one coherent service. This repo does **not** duplicate any of that —
it does not re-derive severity → action, it does not re-implement the
policy engine, and it is not a general-purpose "orchestrator."

It owns exactly one responsibility: segregation of duties between
*deciding* a containment action is warranted (LogSentinel) and
*authorizing* it to actually run (a human, recorded here).

```
LogSentinel                          Approval Service
────────────                         ────────────────
detect → policy decision
   │
   ├─ requires_approval? ──POST /approvals──▶  pending record
   │                                              │
   │                                        human reviews
   │                                        in dashboard
   │                                              │
   │                                        approve / deny
   │                                        (actor + reason,
   │                                         permanently logged)
   │
   ◀────────GET /approvals?status=approved──────┘
   │
executor checks approval
before running "contain"
```

If the approval service is unreachable, LogSentinel's client fails
**closed** — no approval record means the action does not execute.

## What this is not

- Not a correlation/incident engine. There's one detection source right
  now; grouping events into campaigns is real future work but doesn't
  exist yet, here or in LogSentinel, and building it before there's a
  second signal source to justify it would be premature.
- Not a policy engine. If you find yourself adding severity/confidence
  thresholds here, that belongs in LogSentinel's `response/policy.py`
  instead.

## Endpoints

- `POST /approvals` — LogSentinel calls this when policy flags
  `requires_approval=True`
- `GET /approvals?status=pending|approved|denied` — the queue
- `GET /approvals/{id}` — one record, full audit trail
- `POST /approvals/{id}/decide` — `{actor, decision, reason}`. Once
  decided, an approval cannot be re-decided (409) — protects the audit
  record from being silently overwritten by a double-click or a second
  reviewer disagreeing after the fact.
- `GET /health`
- `GET /` — dashboard (pending/approved/denied tabs, approve/deny with a
  reason prompt, auto-refreshes every 10s)

## Running it

```bash
pip install -r requirements.txt
uvicorn orchestrator.main:app --reload --port 8001
```

Open `http://localhost:8001/` for the dashboard.

## Wiring up LogSentinel

Copy `logsentinel_integration/approval_client.py` into LogSentinel's
`backend/app/response/`, then in `executor.py`:

```python
from .approval_client import request_approval, check_approval

# when policy.evaluate_event() returns requires_approval=True:
request_approval(event, decision)

# before executing "contain":
if requires_approval and not check_approval(event["event_id"]):
    return ExecutionResult(status="pending_approval", ...)
```

Set `APPROVAL_SERVICE_URL` in LogSentinel's environment to point at
wherever this service is deployed (defaults to `http://localhost:8002`).

## Testing

```bash
pytest tests/ -v
```

12 tests: creation, listing/filtering by status, approve, deny, the
409 re-decide guard, validation, and that the dashboard actually serves.

## Docker

```bash
docker build -t approval-service .
docker run -p 8001:8001 approval-service
```

## Roadmap (only if actually needed)

- [ ] Real auth for `actor` instead of free-text (needs a user system
      to hook into first)
- [ ] Correlation/incident grouping — once there's a second event
      source worth correlating against
- [ ] Notification on new pending approval (email/Slack webhook)

Maintainer: @Rohit30Confluence · License: MIT
