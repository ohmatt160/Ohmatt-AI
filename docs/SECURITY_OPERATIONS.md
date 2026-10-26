# Security and AI operations

## Sign-in and access control

Roles are evaluated from the current database user record on each authenticated request; a role is not trusted from a long-lived JWT claim. Admin routes must retain server-side authorization checks. The first sign-in and later sign-ins from a different IP address or browser user-agent receive an email one-time-code challenge in production. Accounts with two-factor enabled and admins receive the challenge at every sign-in. The code is generated with a cryptographic random source, stored as a SHA-256 digest, expires after ten minutes, and is consumed after a successful check.

Sign-in and account-creation limits use shared Redis counters so workers enforce one common limit. Production startup requires `RATE_LIMIT_REDIS_URL` and risk-based sign-in challenges enabled. Use a private TLS-enabled Redis service and store its URL in the deployment secret manager. `TRUSTED_PROXY_IPS` must contain only the immediate proxy addresses; otherwise the API ignores `X-Forwarded-For` and uses the network peer address.

## Error and request logs

API errors return a generic message and an `error_id`; the same ID is in `X-Error-ID` and in the server log. Validation responses include field locations and validation types, never submitted values. Request logs include a request ID, method, path, status, and duration. Logs go to standard output/error so the hosting platform can collect, search, retain, and alert on them. Never add authorization headers, passwords, one-time codes, transaction payloads, or raw request bodies to log fields.

The backend CI workflow runs backend tests for each push and pull request. `test_api_route_smoke.py` issues an anonymous request to every documented API method/path and fails on unhandled server errors; feature tests cover critical authenticated service paths. The separate Vercel frontend repository builds the web app on each deployment. Add authenticated success and failure cases when adding or changing route behavior; smoke coverage does not replace feature-level authorization tests.

## Transaction categories and AI assistance

Transaction descriptions first use a small deterministic merchant/descriptor map. A trained artifact is used only when it loads successfully and has confidence of at least 0.35. Unknown descriptions are stored as `Other` with low confidence so they remain reviewable instead of silently appearing as a confident model result. User corrections remain authoritative.

Ohmatt uses the current month as the default period for broad expense questions. It recognizes today, this week, last week, and last month; explicit all-time or merchant-specific questions search all history. The verified context names the period and only includes aggregates and transaction details from that scope. Periods are currently calculated in UTC; timezone-aware local-day boundaries are a follow-up before claiming local-calendar accuracy.

Dashboard insights are calculated from month-to-date and prior-month database aggregates. They do not make a network call during transaction creation, so transaction writes do not wait on an LLM provider. Conversational assistance continues to use the configured Groq service with bounded user-owned history and verified ledger context.
Online model retraining is intentionally disabled in this release. The former endpoint trained one shared model directly from every user's corrected transaction descriptions and wrote model artifacts in the running application. That was unsafe for privacy and inconsistent across workers. Transaction categorization now uses deployed artifacts only when valid, plus deterministic descriptor rules; unknown transactions are labeled `Other` with low confidence.
Admin accounts always receive a sign-in code challenge. If a user has not verified the email address used for sign-in, risk-based or configured two-factor challenges fail closed and ask them to verify the address first.
