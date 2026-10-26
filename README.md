---
title: Ohmatt Finance API
sdk: docker
app_port: 7860
---

# Ohmatt Finance API

## AI Personal Context

The shared, user-scoped AI memory and conversation design, deletion behavior, API endpoints, and integration rules are documented in [docs/AI_PERSONAL_CONTEXT.md](docs/AI_PERSONAL_CONTEXT.md).

Security controls, production Redis requirements, error logging, CI checks, transaction categories, and AI date scopes are documented in [docs/SECURITY_OPERATIONS.md](docs/SECURITY_OPERATIONS.md).

FastAPI backend for the Ohmatt Finance beta.

Health check:

```text
/health
```

API prefix:

```text
/api/v1
```

Deployment instructions are in `DEPLOYMENT.md`.
