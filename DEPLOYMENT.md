# Beta Deployment

This repo deploys as two services:

- Frontend: Vercel, from `app/templates/app`
- Backend: Hugging Face Space, from the repo root using `Dockerfile`

## Backend On Hugging Face

Create a Docker Space and point it at this repository. The backend listens on port `7860`.

Set these Space secrets:

```env
ENV=production
PORT=7860
AUTO_SEED_GEO=true
DATABASE_URL=sqlite:////data/ohmatt.db
SECRET_KEY=replace-with-a-long-random-secret
JWT_SECRET_KEY=replace-with-a-different-long-random-secret
ADMIN_EMAILS=admin@example.com
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=replace-with-a-strong-temporary-password
BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
FRONTEND_URL=https://your-vercel-app.vercel.app
NVIDIA_API_KEY=replace-with-your-nvidia-api-key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

On the first production boot, `BOOTSTRAP_ADMIN_EMAIL` creates or promotes that account to admin and sets its password. After you confirm login works, rotate/remove `BOOTSTRAP_ADMIN_PASSWORD` if you do not want startup to keep resetting that password.

For beta, SQLite can work with Hugging Face persistent storage mounted at `/data`.
For a larger beta, switch `DATABASE_URL` to a managed Postgres/MySQL database.

Password reset, verification, and 2FA emails use `FRONTEND_URL` and SendGrid. Add these secrets on Hugging Face for real emails:

```env
SENDGRID_API_KEY=replace-with-sendgrid-api-key
SENDGRID_FROM_EMAIL=no-reply@example.com
SENDGRID_FROM_NAME=Ohmatt
EMAIL_TOKEN_EXPIRATION=86400
```

`SENDGRID_FROM_EMAIL` must be a verified sender in SendGrid. For a closed beta without email delivery, you can temporarily set `PASSWORD_RESET_LINK_RESPONSE_ENABLED=true`; the API will return the reset link to the frontend after the user requests it. Turn it off before a public launch.

Health check:

```text
https://YOUR-HUGGINGFACE-SPACE.hf.space/health
```

API base:

```text
https://YOUR-HUGGINGFACE-SPACE.hf.space/api/v1
```

## Frontend On Vercel

Deploy from:

```text
app/templates/app
```

Set this Vercel environment variable:

```env
VITE_API_URL=https://YOUR-HUGGINGFACE-SPACE.hf.space/api/v1
```

Build settings:

```text
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
```

The included `vercel.json` handles client-side routing.

## Preflight

From `app/templates/app`:

```bash
npm run check
npm run build
```

From repo root:

```bash
python -m py_compile app/main.py app/config.py app/routes/messages.py app/routes/transactions.py
```

Do not deploy `.env`, local database files, or real secrets to git.
