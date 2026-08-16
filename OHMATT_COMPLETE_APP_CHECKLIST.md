# Ohmatt Complete App Implementation Checklist

Last updated: 2026-07-13

Architecture source: `C:\Users\mattw\Downloads\ohmattos\OHMATTOS_SYSTEM.md`

This is the master checklist for making Ohmatt a secure, tenant-aware, production-ready fintech application across web, mobile, API, and OhmattOS. Check an item only after its acceptance criteria and tests pass under production-equivalent controls.

## How to use this document

- `[x]` means a baseline was confirmed by code inspection. Hardening work may still remain.
- `[ ]` means not implemented, not verified, or not production ready.
- **App** means this repository owns the feature and data.
- **OhmattOS** means the shared infrastructure service owns it.
- **Shared** means both systems need versioned contracts and contract tests.
- **P0** is required before production or before enabling the affected feature.
- **P1** is required for a complete enterprise product. **P2** is a maturity improvement.

## Architecture boundaries

- [ ] **App | P0** Record an ADR confirming that Ohmatt owns users, tenants, memberships, authorization, SSO configuration, sessions, consent, bank connections, balances, and transactions.
- [ ] **OhmattOS | P0** Record that OhmattOS owns shared delivery/infrastructure: email, SMS, push, jobs, retries, dead letters, feature flags, analytics intake, central logs, exports, storage, webhook delivery, and billing infrastructure.
- [ ] **Shared | P0** Version every API/webhook contract, including schemas, authentication, idempotency, timeouts, retries, and deprecation.
- [ ] **App | P0** Keep OhmattOS API keys server-side. Never ship them to web or mobile clients.
- [ ] **App | P0** Never use OhmattOS administrator sessions as Ohmatt user sessions.
- [ ] **App | P0** Use maintained security/protocol libraries or a dedicated identity provider. Do not hand-roll SAML signatures, OIDC verification, WebAuthn, password hashing, or encryption.

**Gate:** each data domain has one system of record, secrets remain server-side, and automated contract tests prove both systems agree on success and failure behavior.

## Production-only delivery policy

- [x] **Shared | P0** Maintain local development and one production deployment; do not create a separate staging deployment.
- [ ] **Shared | P0** Register production integrations disabled by default and activate them only after their security gates pass.
- [ ] **Shared | P0** Use dedicated internal test tenants/users that cannot access real customer data.
- [ ] **Shared | P0** Restrict initial SendGrid/Twilio tests to approved internal destinations and non-marketing content.
- [ ] **Shared | P0** Put new behavior behind server-enforced feature flags with an immediate kill switch.
- [ ] **Shared | P0** Release with backward-compatible migrations, canary activation, health/error thresholds, and a rehearsed rollback.
- [ ] **Shared | P0** Never use real customer traffic as the first test of authentication, authorization, financial sync, notification, or migration changes.

## Current baseline found in code

- [x] Registration, password login, password-strength checks, and password reset exist.
- [x] Email verification token issuance and verification routes exist.
- [x] Password-reset requests use a non-enumerating response.
- [x] JWTs are backed by server-side session records with JTI, idle timeout, refresh, and revocation.
- [x] Current-session and all-session revocation endpoints exist.
- [x] HTTP-only cookie authentication is present.
- [x] Email-based six-digit 2FA exists as a baseline.
- [x] Activity logging and rate limiting exist on several sensitive routes.
- [x] User export and account deletion flows exist as a baseline.
- [x] Bank connections, transactions, budgets, receipts, messages, and AI features exist.
- [x] A server-only OhmattOS client and durable database outbox exist behind `OHMATTOS_ENABLED`.
- [x] OhmattOS notification/SMS acceptance is app-scoped and idempotent, with bounded worker retries.
- [ ] No tenant/organization, membership, tenant role, or tenant permission foundation exists yet.
- [ ] No tenant OIDC, SAML, domain discovery, or SCIM exists yet.
- [ ] No verified phone-number and SMS verification lifecycle exists yet.
- [ ] Current email 2FA is not production ready: challenge state is stored in user preferences rather than a hashed, attempt-limited record.
- [ ] Critical email/SMS delivery is not yet durably routed through OhmattOS with provider status and retries.

# P0 Production Gates

## 1. Tenant foundation and isolation

- [ ] **App | P0** Add `tenants`: ID, name, slug, status, plan, locale, timezone, currency, timestamps, and deletion state.
- [ ] **App | P0** Add `tenant_domains`: normalized domain, verification challenge/state, verified time, and uniqueness guarantees.
- [ ] **App | P0** Add `memberships`: global user, tenant, status, role, inviter, joined time, and removal time.
- [ ] **App | P0** Add invitations with hashed single-use tokens, expiry, resend limits, intended email/domain, role, and acceptance audit events.
- [ ] **App | P0** Adopt one global identity with multiple tenant memberships, unless an ADR justifies a different model.
- [ ] **App | P0** Add `tenant_id` to every tenant-owned bank, account, transaction, budget, receipt, conversation, message, report, export, file, notification, and audit record.
- [ ] **App | P0** Backfill existing records into an explicit default tenant with a reversible tested migration.
- [ ] **App | P0** Add tenant-aware unique constraints, foreign keys, and indexes.
- [ ] **App | P0** Resolve tenant context from authenticated membership and verified routing context, not only an untrusted body/header/query value.
- [ ] **App | P0** Centralize tenant authorization in dependencies/policies.
- [ ] **App | P0** Tenant-scope reads, writes, aggregates, jobs, cache keys, exports, search, analytics, files, and AI retrieval.
- [ ] **App | P0** Add PostgreSQL row-level security for high-value tenant tables, or approve an ADR documenting equivalent defense in depth.
- [ ] **App | P0** Add cross-tenant isolation tests for every identity, financial, file, export, support, and AI service.
- [ ] **App | P0** Make platform support access time-bound, approved, tenant-scoped, and audited.

**Gate:** another tenant's records cannot be read, changed, inferred, cached, exported, searched, or retrieved by AI through API, worker, or direct database integration tests.

## 2. Roles and permissions

- [ ] **App | P0** Replace binary `is_admin` authorization with tenant-scoped roles and permissions.
- [ ] **App | P0** Add `roles`, `permissions`, and `role_permissions`, including immutable system roles and optional custom roles.
- [ ] **App | P0** Define least-privilege owner, admin, finance manager, analyst, support, auditor/read-only, and member roles.
- [ ] **App | P0** Enforce permissions in API and workers; hidden frontend controls are not authorization.
- [ ] **App | P0** Require recent step-up authentication for role/SSO changes, bank disconnection, exports, deletion, support access, and billing changes.
- [ ] **App | P0** Prevent removal/demotion of the last active owner without ownership transfer.
- [ ] **App | P0** Audit membership and policy changes with actor, tenant, target, correlation ID, IP, user agent, and before/after state.

**Gate:** a generated role-permission matrix has deny-by-default tests and every sensitive decision is auditable.

## 3. Authentication and sessions

- [ ] **App | P0** Consolidate duplicate auth routes/services into one source of truth.
- [ ] **App | P0** Migrate password hashes to Argon2id with reviewed parameters, rehashing on successful login.
- [ ] **App | P0** Add breached-password screening without sending complete passwords to a third party.
- [ ] **App | P0** Verify production cookies use `HttpOnly`, `Secure`, explicit `SameSite`, narrow scope, and appropriate expiry.
- [ ] **App | P0** Add CSRF protection to all state-changing cookie-authenticated endpoints.
- [ ] **App | P0** Rotate session IDs after login, MFA, password changes, privilege changes, and SSO authentication.
- [ ] **App | P0** Enforce documented idle and absolute lifetimes, stricter for privileged users.
- [ ] **App | P0** Revoke sessions after reset, MFA recovery, disablement, membership removal, SCIM deactivation, or compromise.
- [ ] **App | P0** Add a device/session view with last seen and individual revocation.
- [ ] **App | P0** Keep JWT claims minimal and define signing-key rotation/emergency revocation.
- [ ] **App | P0** Add progressive throttling by account, IP, device, and tenant without creating an easy account-lockout attack.
- [ ] **App | P0** Send security alerts for new devices, recovery, password/MFA/SSO changes, and suspicious activity.
- [ ] **App | P0** Return generic external auth errors while retaining correlation-safe diagnostics.

**Gate:** fixation, theft, CSRF, replay, stale-role, reset, and revocation cases pass on web and mobile.

## 4. Email verification

- [ ] **App | P0** Add `verification_challenges`: user, tenant, purpose, hashed secret, expiry, attempts, consumed time, cooldown, provider message ID, and delivery state.
- [ ] **App | P0** Make tokens securely random, purpose-bound, short-lived, single-use, and stored only as hashes.
- [ ] **App | P0** Add resend verification with cooldown, daily limits, invalidation of older challenges, and a non-enumerating response.
- [ ] **App | P0** Block email-dependent privileges until verification succeeds.
- [ ] **App | P0** Require reverification before primary-email changes; notify old and new addresses.
- [ ] **Shared | P0** Send verification/recovery/security mail through an OhmattOS adapter and durable queue.
- [ ] **OhmattOS | P0** Configure production email, domain authentication, templates, retries, suppression/bounce handling, delivery webhooks, and dead letters.
- [ ] **Shared | P0** Correlate app challenge IDs and OhmattOS notification IDs without logging secrets.
- [ ] **App | P0** Show pending, delayed, bounced, expired, consumed, and support-required states.

**Gate:** provider outages cannot lose requests; replay/expiry/resend abuse fail safely; delivery problems are visible to users and operations.

## 5. SMS and phone verification

- [ ] **App | P0** Add normalized E.164 phone numbers with country, verification state/time, and change history.
- [ ] **App | P0** Use hashed single-use OTP challenges with strict expiry and attempts.
- [ ] **App | P0** Add per-user, phone, IP, device, and tenant rate/spend controls.
- [ ] **App | P0** Prevent enumeration and brute force while locking challenges instead of whole accounts where practical.
- [ ] **App | P0** Record purpose and required consent for transactional versus marketing messages.
- [ ] **Shared | P0** Ohmatt owns verification state; OhmattOS owns delivery state and provider integration.
- [ ] **OhmattOS | P0** Configure primary and controlled failover SMS providers, delivery receipts, cost monitoring, and dead letters.
- [ ] **App | P0** Never use SMS possession alone to authorize high-risk financial actions.
- [ ] **App | P0** Add secure phone-change and recovery flows with alerts to existing verified channels.

**Gate:** OTPs are never logged/plaintext-stored, retries do not create duplicate valid challenges, and abuse/cost tests pass.

## 6. MFA, recovery, and passkeys

- [ ] **App | P0** Replace plaintext 2FA state in preferences with hashed challenge records.
- [ ] **App | P0** Add TOTP with encrypted secrets, replay prevention, and bounded clock skew.
- [ ] **App | P0** Add one-time recovery codes stored only as hashes and displayed once.
- [ ] **App | P0** Require recent authentication plus an existing factor or reviewed recovery before disabling/resetting MFA.
- [ ] **App | P0** Require MFA for platform admins, tenant owners/admins, and support impersonation.
- [ ] **App | P1** Add passkeys/WebAuthn: enrollment, naming, discoverable credentials, revocation, backup state, and recovery.
- [ ] **App | P1** Add tenant policies for required/allowed factors and phishing-resistant MFA.

## 7. Secrets, encryption, and privacy

- [ ] **App | P0** Inventory bank tokens, SSO secrets, SAML keys, MFA seeds, webhooks, API keys, provider credentials, and sensitive PII.
- [ ] **App | P0** Encrypt sensitive database fields with authenticated encryption and keys separate from the database.
- [ ] **App | P0** Remove bank/provider credentials from plaintext storage and support versioned key rotation.
- [ ] **Shared | P0** Store service credentials only in deployment secret managers, never source control/client bundles.
- [ ] **Shared | P0** Document rotation, revocation, break-glass, and compromise runbooks.
- [ ] **App | P0** Redact headers, cookies, tokens, OTPs, financial IDs, SSO assertions, and unnecessary PII from logs/traces.
- [ ] **App | P0** Classify data and set retention/deletion rules for identity, finance, AI, support, audit, and telemetry.
- [ ] **App | P0** Ensure export/deletion covers tables, files, caches, search, backups policy, and AI/vector stores.
- [ ] **App | P0** Complete a privacy impact assessment and legal review for actual activities/jurisdictions.

**Gate:** database/log snapshots expose no reusable credentials, and a tested inventory traces every sensitive datum through storage, transmission, retention, and deletion.

## 8. Fintech data integrity and bank sync

- [ ] **App | P0** Define canonical provider-independent account, balance, and transaction schemas.
- [ ] **App | P0** Store provider record/account IDs, source, raw reference, state, amount, currency, timestamps, and ingestion version for every transaction.
- [ ] **App | P0** Use provider IDs, stable deduplication, and constraints so retries cannot duplicate transactions.
- [ ] **App | P0** Model pending-to-posted transitions without losing provenance or double-counting.
- [ ] **App | P0** Store balance type, currency, provider timestamp, fetched time, and freshness. Never label an estimate as a bank-reported balance.
- [ ] **App | P0** Track every sync run: cursor/window, expected/fetched pages, counts, retries, errors, and reconciliation result.
- [ ] **App | P0** Exhaust pagination and persist cursors only after associated records commit.
- [ ] **App | P0** Add initial-history backfill plus incremental sync, showing provider history limits to users.
- [ ] **App | P0** Reconcile page gaps, unexpected count changes, duplicates, currencies, and stale balances.
- [ ] **App | P0** Authenticate bank webhooks and make processing idempotent, replay-safe, order-tolerant, and asynchronous.
- [ ] **App | P0** Show sync state, last success, balance as-of, limitations, and recoverable connection errors on web/mobile.
- [ ] **App | P0** Record consent scopes, provider, policy version, actor, and grant/revoke times.
- [ ] **App | P0** Revoke provider access/jobs on disconnect, deprovisioning, or consent withdrawal.
- [ ] **App | P0** Add immutable audits for connections, consent, sync, balance refresh, mutation, export, and deletion.

**Gate:** repeated syncs are idempotent, full-history fixtures reconcile exactly, missing pages fail loudly, freshness is truthful, and no bank secret reaches clients or AI.

## 9. AI access to financial data

- [ ] **App | P0** Give AI access only through tenant/user-authorized data services, never unrestricted tables.
- [ ] **App | P0** Provide complete transaction access using deterministic pagination/aggregation; disclose any provider history limit.
- [ ] **App | P0** Attach source transaction IDs and calculation metadata so financial answers are reproducible.
- [ ] **App | P0** Prohibit invented transactions, balances, merchants, categories, and dates. Missing data must produce an explicit data-gap response.
- [ ] **App | P0** Compute totals, balances, budgets, and trends in tested code/SQL, not natural-language generation.
- [ ] **App | P0** Define inclusion of pending, reversed, duplicate, refunded, transferred, and multi-currency transactions.
- [ ] **App | P0** Compare source counts/totals with selected context counts/totals before generation.
- [ ] **App | P0** Defend tools/retrieval against prompt injection, cross-tenant references, over-broad queries, and unauthorized exports.
- [ ] **App | P0** Redact secrets/unneeded identifiers and document model-provider retention/training settings.
- [ ] **App | P0** Log model/tool/calculation versions and source IDs/counts without logging sensitive prompts by default.
- [ ] **App | P0** Add golden exactness tests for totals, pagination, state transitions, refunds, duplicates, currencies, and missing data.

**Gate:** every factual financial answer is reproducible from authorized records, completeness checks pass, and incomplete history is stated instead of guessed.

## 10. OhmattOS integration

- [ ] **OhmattOS | P0** Register separate local-development and production app records and credentials.
- [ ] **OhmattOS | P0** Issue least-privilege credentials with owner, rotation, and revocation.
- [x] **App | P0** Build the typed OhmattOS server adapter baseline with bounded timeouts, classified retry behavior, and structured errors. Circuit-breaker metrics remain before broad activation.
- [x] **App | P0** Add a transactional outbox so user registration and notification intent cannot diverge.
- [ ] **Shared | P0** Define callback signatures, timestamp tolerance, replay storage, idempotency, retries, and dead-letter ownership.
- [ ] **Shared | P0** Add contract tests for each notification, job, webhook, flag, analytics, log, export, storage, and billing API used.
- [x] **OhmattOS | P0** Resolve worker documentation inconsistency; verify SQLite and PostgreSQL builds, conditional claims, stale-claim recovery, and bounded retries.
- [ ] **OhmattOS | P0** Finish real email/SMS providers, queue retries, delivery webhooks, and dead-letter operations.
- [ ] **OhmattOS | P0** Add audit logs, RBAC, secrets-at-rest encryption, per-app CORS, key rotation, and alerts.
- [ ] **Shared | P0** Ensure login/auth does not require synchronous OhmattOS availability when durable local acceptance is possible.
- [ ] **Shared | P0** Monitor failures, latency, queue age, retries, dead letters, provider cost, and webhook health.

## 11. Neon/PostgreSQL and migrations

- [ ] **App | P0** Standardize one migration framework with forward and rollback/repair procedures.
- [ ] **App | P0** Run migration CI against fresh and sanitized production-shaped databases.
- [ ] **App | P0** Use expand/migrate/contract releases for breaking changes.
- [ ] **App | P0** Configure Neon pooling and cap pool size per API/worker process and environment.
- [ ] **App | P0** Add statement, lock, idle-transaction, connection, and downstream timeouts.
- [ ] **App | P0** Add measured indexes for tenant/user, bank account/connection, transaction date/state, session JTI, challenge expiry, and outbox status.
- [ ] **App | P0** Remove N+1 access from transaction, dashboard, membership, and admin APIs.
- [ ] **App | P0** Use cursor/keyset pagination for large transaction, audit, notification, and member lists.
- [ ] **App | P0** Add constraints for ownership, money precision, currency, transaction identity, membership, challenge state, and referential integrity.
- [ ] **App | P0** Store money as fixed-precision decimal/minor units, never binary floating point.
- [ ] **App | P0** Test backups/PITR against documented RPO/RTO with quarterly restore drills.
- [ ] **App | P0** Monitor slow queries, locks, saturation, migration failures, and table/index growth.

## 12. API security and reliability

- [ ] **App | P0** Publish a versioned API contract and consistent error envelope with correlation IDs.
- [ ] **App | P0** Bound and validate all bodies, queries, headers, files, and pagination.
- [ ] **App | P0** Enforce object/function authorization in routes and workers.
- [ ] **App | P0** Require idempotency keys for retried financial and account-management mutations.
- [ ] **App | P0** Set body/upload/concurrency/request/downstream limits.
- [ ] **App | P0** Use exact per-environment CORS origins; credentialed CORS never uses wildcard origins.
- [ ] **App | P0** Add CSP, HSTS, content-type protection, frame restrictions, and restrictive referrer policy.
- [ ] **App | P0** Validate uploaded type/content, scan malware, use private storage, and issue short-lived signed access.
- [ ] **App | P0** Separate liveness from dependency readiness without leaking configuration.
- [ ] **App | P0** Define SLOs for auth, sync acceptance, transaction reads, AI answers, and exports.
- [ ] **App | P0** Make caches tenant-aware, authorization-safe, invalidated, and tested before use.
- [ ] **App | P0** Rate/spend-limit exports, AI, sync, auth, verification, invitations, and SSO discovery.

# P1 Enterprise Identity

## 13. Tenant OIDC SSO

- [ ] **App | P1** Add encrypted tenant `sso_connections`: type, status, domains, issuer, client, secret, scopes, mappings, and enforcement.
- [ ] **App | P1** Implement Authorization Code + PKCE with cryptographic state/nonce and one-time short-lived login transactions.
- [ ] **App | P1** Validate exact issuer, signature, audience, authorized party where needed, nonce, expiry, and not-before.
- [ ] **App | P1** Cache discovery/JWKS safely and refresh on unknown key ID.
- [ ] **App | P1** Prevent SSRF from issuer/metadata URLs to private, link-local, and metadata networks.
- [ ] **App | P1** Map stable subject, verified email, name, and groups; never identify solely by mutable email.
- [ ] **App | P1** Store external links as `(tenant, connection, issuer, subject)`.
- [ ] **App | P1** Define JIT/account-linking policy; never merge solely on unverified email.
- [ ] **App | P1** Add test, staged enablement, rollback, diagnostics, and audit events.
- [ ] **App | P1** Support SSO enforcement with explicit phishing-resistant break-glass accounts.

## 14. Tenant SAML 2.0 SSO

- [ ] **App | P1** Implement Ohmatt as a service provider using a maintained library/broker.
- [ ] **App | P1** Generate per-environment SP metadata, entity ID, ACS, signing/encryption certificates, and rotation.
- [ ] **App | P1** Safely import IdP metadata with reviewed manual fallback.
- [ ] **App | P1** Validate signatures, status, issuer, audience, recipient, destination, `InResponseTo`, time conditions, and replay.
- [ ] **App | P1** Harden XML parsing against external entities, expansion, wrapping, and ambiguous signatures.
- [ ] **App | P1** Reject weak/unknown algorithms and enforce signed response/assertion policy.
- [ ] **App | P1** Make RelayState opaque/integrity-protected and block arbitrary redirects.
- [ ] **App | P1** Add stable NameID/attribute mappings and external identity links.
- [ ] **App | P1** Disable IdP-initiated SSO by default or document/test its reduced correlation guarantees.
- [ ] **App | P1** Add certificate overlap, expiry alerts, metadata refresh, and diagnostics.
- [ ] **App | P1** Define SLO behavior; local logout/revocation must work independently.

## 15. SSO discovery and UX

- [ ] **App | P1** Route by verified domain, tenant slug, invitation, or organization URL.
- [ ] **App | P1** Do not reveal private tenant membership/configuration during discovery.
- [ ] **App | P1** Define domains shared by multiple tenants.
- [ ] **App | P1** Preserve tenant and only allowlisted post-login destinations.
- [ ] **App | P1** Sanitize tenant branding and prohibit arbitrary HTML/CSS/script.
- [ ] **App | P1** Handle required SSO, unavailable IdP, expired config, unverified domain, disabled membership, and support states.
- [ ] **App | P1** Re-evaluate permissions and clear tenant caches/state when switching tenants.

## 16. SCIM 2.0

- [ ] **App | P1** Issue tenant-scoped SCIM credentials stored as hashes with scopes, expiry, rotation, last use, and revocation.
- [ ] **App | P1** Implement supported service configuration, schemas, and resource types.
- [ ] **App | P1** Implement `/Users` create/read/replace/patch/filter/paginate/activate/deactivate.
- [ ] **App | P1** Implement `/Groups` only where group-to-role behavior is explicitly supported.
- [ ] **App | P1** Return SCIM errors, ETags/resource versions, and idempotent outcomes.
- [ ] **App | P1** Uniquely constrain `externalId` within tenant/provider scope.
- [ ] **App | P1** Deactivation disables membership, revokes sessions/jobs/access, and preserves required financial/audit records.
- [ ] **App | P1** Prevent SCIM from deleting the last owner or granting prohibited privilege.
- [ ] **App | P1** Audit provisioning without logging bearer tokens.
- [ ] **App | P1** Add provider compatibility and bulk/rate tests.

## 17. Tenant administration

- [ ] **App | P1** Add profile, domains, members, invitations, roles, security, sessions, SSO, SCIM, billing, integrations, audit, retention, exports, and deletion settings.
- [ ] **App | P1** Make SSO setup draft -> validate -> test -> activate -> enforce -> rollback while preserving the current admin session.
- [ ] **App | P1** Issue/rotate/revoke SCIM secrets with one-time display.
- [ ] **App | P1** Provide immutable audit search/export with least-privilege access.
- [ ] **App | P1** Require step-up/approval for high-risk tenant changes.
- [ ] **App | P1** Build support tools that cannot silently bypass tenant boundaries.

# Product and Operations Completeness

## 18. Lifecycle, notifications, and billing

- [ ] **App | P1** Complete invite, join, leave, suspend, reactivate, ownership transfer, and member removal.
- [ ] **App | P1** Define personal versus tenant-owned financial data behavior when users leave/delete identities.
- [ ] **App | P1** Add reviewed recovery with cooling-off periods for high-risk changes and security history.
- [ ] **Shared | P1** Version notification events/templates across email, SMS, push, and in-app channels.
- [ ] **App | P1** Store channel preferences with mandatory-security-message exceptions.
- [ ] **OhmattOS | P1** Add localized templates, approval/versioning, failover, suppression, and delivery analytics.
- [ ] **Shared | P1** Make retries user-visible only once through idempotency.
- [ ] **App | P1** Add a tenant-aware in-app notification inbox.
- [ ] **Shared | P1** Decide the billing system of record and document ownership.
- [ ] **App | P1** Model plans, subscriptions, trials, seats, usage, grace periods, and entitlements.
- [ ] **App | P1** Enforce entitlements in API/workers, not only UI.
- [ ] **Shared | P1** Sign, replay-protect, idempotently process, and periodically reconcile billing webhooks.
- [ ] **App | P1** Add billing admin, invoices, payment recovery, cancellation, and post-expiry data-access policy.
- [ ] **App | P1** Confirm PCI DSS scope without storing card data unnecessarily.

## 19. Web and mobile UX

- [ ] **App | P0** Audit light/dark contrast for text, controls, focus, charts, disabled states, errors, and financial statuses.
- [ ] **App | P0** Test mobile widths/safe areas; feedback/support controls must never cover send or other primary actions.
- [ ] **App | P0** Add consistent loading, empty, offline, partial, stale, denied, expired-session, error, and retry states.
- [ ] **App | P0** Show bank source, freshness, sync progress, and reconciliation status without implying false completeness.
- [ ] **App | P1** Meet WCAG 2.2 AA for keyboard, focus, semantics, contrast, zoom/reflow, motion, errors, and screen readers.
- [ ] **App | P1** Securely preserve auth/SSO through allowlisted mobile app/deep links.
- [ ] **App | P1** Add tenant context, switcher, and role-aware navigation on financial screens.
- [ ] **App | P1** Require clear impact confirmation/recent auth for destructive actions.
- [ ] **App | P1** Add desktop/mobile and light/dark visual regression tests.

## 20. Observability and incidents

- [ ] **Shared | P0** Propagate correlation IDs through client, API, DB logs, OhmattOS, workers, providers, and webhooks.
- [ ] **Shared | P0** Add redacted structured logs, metrics, and traces with tenant-safe cardinality.
- [ ] **App | P0** Alert on auth anomalies, SSO failures, sync gaps, reconciliation failures, stale balances, replay, queue lag, DB saturation, and authorization denials.
- [ ] **App | P0** Write runbooks for leaked credentials, tenant exposure, account takeover, provider/DB/OhmattOS outage, and transaction gaps.
- [ ] **App | P0** Define on-call ownership, severity, customer notices, evidence preservation, and postmortems.
- [ ] **Shared | P1** Add OpenTelemetry-compatible tracing and dashboards.
- [ ] **App | P1** Add synthetic registration, verification, login, SSO, bank sync, transaction read, and notification checks.
- [ ] **App | P1** Exercise disaster recovery and provider failover.

## 21. Secure software delivery

- [ ] **App | P0** Require format/lint/type/unit/integration/migration/build checks for API, web, and mobile.
- [ ] **App | P0** Pin runtimes/dependencies; align lockfiles and deployment roots with the moved structure.
- [ ] **App | P0** Add dependency, secret, SAST, container, and infrastructure scans with severity policy.
- [ ] **App | P0** Produce an SBOM for releases.
- [ ] **App | P0** Keep local-development data/keys separate from production, and isolate internal production test identities from customers.
- [ ] **App | P0** Protect branches and production rights; review migrations.
- [ ] **App | P0** Add canary/gradual rollout, feature flags, rollback, and mobile/API compatibility policy.
- [ ] **App | P0** Block release on failed isolation, auth, reconciliation, restore, or contract gates.

## Test matrix

- [ ] **P0** Unit tests: auth policies, challenges, permissions, normalization, reconciliation, and deterministic finance calculations.
- [ ] **P0** PostgreSQL integration tests: constraints, migrations, concurrency, rollback, and Neon-compatible behavior.
- [ ] **P0** Isolation tests: user/membership/tenant context, object IDs, cache, jobs, exports, files, AI, and admin.
- [ ] **P0** OhmattOS consumer/provider contract tests.
- [ ] **P0** End-to-end: register, verify/resend, login/reset/MFA, invite/role, connect, initial/incremental sync, disconnect.
- [ ] **P0** Security: enumeration, brute force, CSRF, XSS, SSRF, injection, IDOR, replay, fixation, redirects, uploads, and log leakage.
- [ ] **P0** Financial fixtures: exact counts/totals across pagination, retries, transitions, duplicates, refunds, and currencies.
- [ ] **P1** OIDC/SAML positive and negative interoperability fixtures for representative IdPs.
- [ ] **P1** SCIM provider compatibility tests.
- [ ] **P1** Accessibility, visual, browser/device, deep-link, network-loss, timezone, and locale tests.
- [ ] **P1** Load/soak: auth bursts, SSO callbacks, transaction lists, webhooks, sync, AI, exports, and queues.
- [ ] **P1** Failure/chaos: timeouts, duplicate/out-of-order webhooks, queue outage, DB failover, partial migration, and OhmattOS outage.

## Required launch evidence

- [ ] Threat model/data flows cover web, mobile, API, OhmattOS, Neon, bank/identity/AI/notification providers, and storage.
- [ ] Approved asset inventory and data classification.
- [ ] Passing tenant isolation and authorization report with no unresolved critical/high findings.
- [ ] Independent penetration test covering auth, SSO, tenant isolation, API, web/mobile, bank integration, and business logic.
- [ ] SAST/dependency/secret/container/infrastructure scans meet release policy.
- [ ] Backup restoration and disaster recovery meet documented RPO/RTO.
- [ ] Sync reconciliation proves no silent transaction loss within supported history windows.
- [ ] Privacy notices, consent, retention, subprocessors, deletion, and export procedures are reviewed.
- [ ] Incident/breach/vulnerability disclosure/on-call procedures are exercised.
- [ ] Engineering, security, operations, and product sign production readiness.

## Delivery milestones

### M0 - Stabilize

- [ ] Reproducible clean installs and production builds after the folder move.
- [ ] Migration CI, PostgreSQL tests, production-safe internal validation, secret inventory, and release gates.
- [ ] Consolidated auth and documented current data flows.

### M1 - Tenant core

- [ ] Tenants, domains, memberships, invitations, RBAC, tenant context, and backfill.
- [ ] Tenant-scope every domain and pass isolation tests.

### M2 - Verification and OhmattOS

- [ ] Secure challenges, email resend, phone/SMS lifecycle, typed adapter, transactional outbox, and contract tests.
- [ ] Production email/SMS delivery, receipts, retries, and dead letters.

### M3 - Sessions and MFA

- [ ] Cookie/CSRF/session hardening, device management, TOTP, recovery codes, alerts, and privileged MFA.

### M4 - OIDC

- [ ] Tenant configuration, discovery, login, linking/JIT, enforcement, diagnostics, and conformance tests.

### M5 - SAML

- [ ] SP metadata, assertion validation, mapping, certificate rotation, enforcement, diagnostics, and security tests.

### M6 - SCIM and tenant admin

- [ ] Users/groups, deprovisioning, security admin, audit views, and compatibility tests.

### M7 - Fintech and AI assurance

- [ ] Canonical ingestion, exhaustive sync, reconciliation, balance freshness, consent, AI provenance, and exactness tests.

### M8 - Launch readiness

- [ ] Billing, UX/accessibility, observability, load/failure tests, restore, penetration test, legal/compliance review, and sign-off.

## First ten implementation tickets

1. [ ] ADRs: ownership, tenancy, global identity/membership, and SSO build-versus-buy.
2. [ ] Migrations: tenants, memberships, domains, invitations, roles, permissions, and tenant context.
3. [ ] Backfill a default tenant and tenant-scope repositories/APIs.
4. [ ] Add cross-tenant access tests before tenant administration is exposed.
5. [ ] Add secure verification challenges, resend, phone models, and replace plaintext 2FA state.
6. [x] Build the typed OhmattOS adapter, transactional outbox, sibling contract, and baseline contract tests.
7. [ ] Encrypt bank credentials and other application secrets with rotation.
8. [ ] Add sync-run tracking, exhaustive pagination, reconciliation, and truthful balance freshness.
9. [ ] Harden cookies, CSRF, session rotation/revocation, privileged MFA, and security audits.
10. [ ] Select SSO approach; implement OIDC, then SAML, then SCIM after tenant authorization stabilizes.

## Decisions required

- [ ] **Identity platform:** managed identity broker/mature libraries versus self-operated protocols. Do not build protocol cryptography/parsing from scratch.
- [ ] **Tenant identity:** confirm global identities plus memberships and external identity links.
- [ ] **SSO enforcement:** grace period, break-glass users, and support recovery.
- [ ] **JIT/linking:** domain, verified-email, invitation, and collision rules.
- [ ] **SCIM roles:** group mapping and roles that automation may never grant.
- [ ] **SMS providers:** primary/failover based on Nigerian delivery, sender requirements, receipts, abuse controls, and cost.
- [ ] **Compliance scope:** jurisdictions, customer type, regulated activities, data residency, retention, and card scope with qualified advisers.

## Definition of done for each checkbox

- [ ] Owner and system of record documented.
- [ ] Threats, abuse, privacy, and failure behavior reviewed.
- [ ] Migrations and rollback/repair tested.
- [ ] Authorization is deny-by-default and tenant isolation is covered.
- [ ] Sensitive data is encrypted and redacted.
- [ ] Appropriate unit, integration, contract, end-to-end, and negative tests pass.
- [ ] Metrics, audits, logs, alerts, and diagnostics exist without leaking secrets/PII.
- [ ] Web/mobile loading, empty, stale, offline, error, and recovery states exist.
- [ ] Documentation and runbooks are updated.
- [ ] Disabled-by-default production verification and controlled canary rollout/rollback succeed.

## Primary standards references

- [OpenID Connect specifications](https://openid.net/developers/specs/)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OASIS SAML 2.0 technical overview](https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0-cd-02.html)
- [SCIM protocol - RFC 7644](https://www.rfc-editor.org/rfc/rfc7644)
- [SCIM core schema - RFC 7643](https://www.rfc-editor.org/rfc/rfc7643)
- [Web Authentication Level 3](https://www.w3.org/TR/webauthn-3/)
- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/)
- [PCI Security Standards Council](https://www.pcisecuritystandards.org/standards/pci-dss/)

This checklist is an engineering control document, not legal or regulatory advice. Applicable obligations must be confirmed for the product's actual activities and operating jurisdictions.
