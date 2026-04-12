# SentinelAI Deployment Guide

This guide deploys SentinelAI using Vercel experimental services for frontend and backend.

## Prerequisites

- GitHub repository with this project pushed
- Vercel account
- Optional API keys: OpenAI and VirusTotal

## Step 1: Configure Backend Service

1. Keep the backend service in [vercel.json](vercel.json) pointing at `backend`.
2. Add environment variables:
   - `OPENAI_API_KEY`
   - `VIRUSTOTAL_API_KEY`
   - `SECRET_KEY`
   - `ALLOWED_ORIGINS` if your backend checks CORS
3. Confirm the backend entrypoint is `backend`.

## Step 2: Configure Vercel Services

1. Open [vercel.json](vercel.json).
2. Confirm the frontend entrypoint is `frontend` and the backend route prefix is `/_/backend`.
3. Commit and push.

## Step 3: Deploy Frontend to Vercel

1. Go to Vercel and import your GitHub repository.
2. Vercel will use [vercel.json](vercel.json).
3. Click Deploy.
4. Copy your Vercel URL.

## Step 4: Update Backend CORS

Set this in backend environment variables if you need CORS:

```text
ALLOWED_ORIGINS=https://your-project.vercel.app,http://localhost:5173
```

Save and allow Render to redeploy.

## API Routing Model

- Frontend calls `/_/backend/api/v1/...` by default.
- In production, Vercel routes the backend service at `/_/backend`.
- In local dev, Vite proxy forwards `/api/*` to `http://localhost:8000`.

You can also set `VITE_API_URL` in Vercel if you prefer absolute API URLs.

## Testing

1. Open your Vercel URL.
2. Check app pages and API-backed views.
3. If requests fail, inspect browser network and Render logs.

## Troubleshooting

### API calls return 404 or fail

- Verify the service entrypoints and route prefixes in `vercel.json`.
- Confirm frontend is deployed from the latest commit.

### CORS blocked

- Confirm `ALLOWED_ORIGINS` includes your exact Vercel URL.
- Do not include trailing slash in origins.

### Backend cold starts

- Render free tier may sleep and take 30-60 seconds on first request.

## Production Recommendations

1. Move from SQLite to managed PostgreSQL on Render.
2. Use a long random `SECRET_KEY`.
3. Add monitoring and error tracking.
4. Use paid tiers for predictable performance.
