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
DATABASE_URL=sqlite:////data/ohmatt.db
SECRET_KEY=replace-with-a-long-random-secret
JWT_SECRET_KEY=replace-with-a-different-long-random-secret
BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
NVIDIA_API_KEY=replace-with-your-nvidia-api-key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

For beta, SQLite can work with Hugging Face persistent storage mounted at `/data`.
For a larger beta, switch `DATABASE_URL` to a managed Postgres/MySQL database.

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
