# Ohmatt and OhmattOS Sibling Contract

Contract version: `2026-07-13/v1`

Ohmatt and OhmattOS are sibling applications. They collaborate through authenticated, versioned APIs and events. Neither application reads or writes the other's database.

## Ownership

- Ohmatt owns users, tenants, memberships, authorization, sessions, verification state, consent, bank connections, balances, transactions, and AI-visible financial context.
- OhmattOS owns shared infrastructure execution: queued email/SMS/push delivery, provider adapters, retries, dead-letter operations, webhook delivery, exports, shared telemetry, and other explicitly adopted platform services.
- A provider acceptance or delivery status does not change Ohmatt business state unless Ohmatt processes an authenticated result event.
- OhmattOS user/customer identifiers are opaque external identifiers. They do not authorize access to Ohmatt data.

## Authentication

- Ohmatt calls OhmattOS from its backend only with a dedicated service API key.
- The service key is hashed at rest by OhmattOS and stored only in Ohmatt's backend secret manager.
- The key must never enter Vercel variables exposed to Vite, Flutter/mobile configuration, browser storage, logs, analytics, URLs, or API responses.
- OhmattOS derives the authoritative `app_id` from the service key.
- A caller-supplied `app_id` is optional compatibility data. A mismatch returns `403`.
- Human OhmattOS administrator sessions are never application service credentials.

## Notification Acceptance

Endpoint:

```text
POST /api/v1/notifications/send
X-API-Key: <service-key>
Idempotency-Key: <stable-event-key>
Content-Type: application/json
```

Request:

```json
{
  "app_id": "<registered-ohmatt-app-id>",
  "user_id": "<opaque-ohmatt-user-id>",
  "channel_type": "email",
  "template_id": null,
  "idempotency_key": "<stable-event-key>",
  "content": {
    "to": "<destination>",
    "subject": "<subject>",
    "body": "<plain-text-body>"
  }
}
```

Accepted response:

```json
{
  "success": true,
  "data": {
    "message_id": "<ohmattos-message-id>",
    "status": "queued",
    "deduplicated": false
  },
  "error": null,
  "meta": {
    "request_id": "<correlation-id>",
    "took_ms": 0
  }
}
```

## Reliability Semantics

- Ohmatt commits business state and the outbox intent in one database transaction.
- Ohmatt retries API acceptance with the same idempotency key.
- OhmattOS stores at most one active queue record per app and idempotency key.
- An HTTP timeout has an unknown outcome and must be retried with the same key.
- OhmattOS conditionally claims queue records so concurrent workers cannot intentionally deliver the same row.
- Provider failures use bounded exponential retry. Exhausted messages become `failed` for operations review.
- Stale processing claims are recovered after the configured safety window.
- Delivery remains at-least-once at external-provider boundaries; provider IDs and callbacks must be used for final reconciliation.

## Error Handling

- `400`: invalid request; correct before retry.
- `401`: missing or invalid service key; rotate/fix configuration.
- `403`: attempted cross-app access; security alert and no retry.
- `408`, `425`, `429`, and `5xx`: transient; retry with backoff and the same idempotency key.
- Invalid response envelopes are transient until the retry limit is reached.
- Secrets, OTPs, reset tokens, and complete provider response bodies must not be logged.

## Production-Only Activation

- There is no separate staging deployment.
- Integration code is deployed with `OHMATTOS_ENABLED=false`.
- The production app may be registered before activation.
- First delivery uses dedicated internal users and approved internal destinations.
- Activation requires cross-app isolation tests, successful email/SMS receipt, queue monitoring, and a server-side kill switch.
- Enablement expands by canary cohort; live users are never the first test.
- Rollback disables new dispatch while preserving outbox records for controlled replay.

## Change Rules

- Breaking request/response changes require a new contract version.
- Both repositories and their consumer/provider tests must update in the same release window.
- Fields may be added compatibly; existing required meanings may not silently change.
- SSO, SCIM, billing, storage, analytics, and webhooks must receive their own versioned sections before Ohmatt adopts them.

