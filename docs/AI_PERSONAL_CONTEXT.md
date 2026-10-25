# Personal AI Context

## Design

Ohmatt AI does not fine-tune a separate model for each user. Personalization is retrieved from Ohmatt-owned, user-scoped data at request time. This keeps facts editable and deletable, avoids per-user model jobs, and lets future Ohmatt AI products reuse the same context service.

The context has three distinct sources:

- **Conversation history:** existing `messages` rows between the authenticated user and `ai_assistant`. These are the source of truth for chat history.
- **Saved personal memories:** `ai_personal_memories` rows explicitly created by the user. The model never writes or silently extracts these. They can describe preferences or context, but are not evidence for financial claims.
- **Financial records:** the transaction context service queries the current ledger for each request. Ledger calculations remain authoritative and are never replaced by conversation history or memories.

`AIContextService` is the shared retrieval boundary for future AI features. Every read is scoped to the authenticated `user_id`; feature code must not accept an arbitrary user ID from a client. Current retrieval is intentionally bounded: at most 16 recent chat messages / 8,000 characters and 20 saved memories / 5,000 characters. Saved memories are capped at 50 per user and 500 characters each. This avoids unbounded prompt size and keeps retrieval to indexed database reads without a vector service on the chat hot path.

## Data Lifecycle And API

- `GET /api/v1/messages/ai` returns up to 500 recent current-format messages and up to 500 legacy self-addressed messages.
- `DELETE /api/v1/messages/ai/history` permanently deletes both sides of the AI transcript, including legacy self-addressed chat rows. Saved memories remain.
- `GET /api/v1/messages/ai/memories` lists the caller's saved memories.
- `POST /api/v1/messages/ai/memories` creates a caller-owned memory. Duplicate entries are rejected.
- `DELETE /api/v1/messages/ai/memories/{memory_id}` deletes one memory, with ownership enforced in the query.
- `DELETE /api/v1/messages/ai/data` deletes the caller's AI transcript and saved memories. Financial records are unchanged.
- Account deletion removes saved memories along with the existing user-owned records.
- If a message from the transcript was forwarded to another user's inbox, clearing the source transcript unlinks that reference but does not delete the recipient-owned copy.

The chat UI distinguishes clearing history from deleting all AI data and explains that clearing history preserves memories. It lets users add and remove memories. Memory content is never copied to activity-log metadata.

## Security And Operations

- Chat, memory, clear, and delete endpoints require the existing authenticated-user dependency.
- Memory queries and mutations include `current_user.id` in their database predicates; memory IDs are not treated as authorization.
- Memory rows have a user/time index and a per-user uniqueness constraint. New tables are created additively through the backend's existing SQLAlchemy metadata initialization.
- Only bounded recent conversation and saved memories are sent to the configured Groq provider. The complete transcript and ledger remain in Ohmatt's database; neither is used to fine-tune a per-user model.
- Prompt rules keep saved memories and prior conversation subordinate to verified ledger values and financial safety rules. Transaction descriptions remain untrusted input.
- Deletion endpoints remove AI content data but retain non-content operational/audit events subject to the app's retention policy. They do not delete transactions, bank connections, or bank credentials.

## Future Integration Rule

New AI features should call `ai_context_service.build(...)` from a server-side authenticated flow, use the returned memory context only for personalization, and keep product-specific conversation history separate where appropriate. Do not build another per-feature memory store, expose this service to unauthenticated clients, or feed financial answers from saved memories.
