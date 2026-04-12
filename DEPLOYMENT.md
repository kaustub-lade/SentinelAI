# SentinelAI Deployment Guide

This guide deploys SentinelAI using Vercel for frontend and Render for backend.

## Prerequisites

- GitHub repository with this project pushed
- Vercel account
- Render account
- Optional API keys: OpenAI and VirusTotal

## Step 1: Deploy Backend to Render

1. Open Render and create a new Web Service from your GitHub repo.
2. Use these service settings:
   - Environment: Python 3
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables:
   - `OPENAI_API_KEY`
   - `VIRUSTOTAL_API_KEY`
   - `SECRET_KEY`
   - `ALLOWED_ORIGINS` (set after Vercel URL is known)
   - `DATABASE_URL` (optional override)
4. Deploy and copy your Render backend URL.

## Step 2: Configure Vercel Rewrite Target

1. Open [frontend/vercel.json](frontend/vercel.json).
2. Replace `your-render-backend-url.onrender.com` with your Render backend hostname.
3. Commit and push.

## Step 3: Deploy Frontend to Vercel

1. Go to Vercel and import your GitHub repository.
2. Set Root Directory to `frontend`.
3. Vercel will use [frontend/vercel.json](frontend/vercel.json):
   - Build command: `cd frontend && npm install && npm run build`
   - Output directory: `frontend/dist`
4. Click Deploy.
5. Copy your Vercel URL.

## Step 4: Update Render CORS

Set this in Render environment variables:

```text
ALLOWED_ORIGINS=https://your-project.vercel.app,http://localhost:5173
```

Save and allow Render to redeploy.

## API Routing Model

- Frontend calls `/api/v1/...` by default.
- In production, Vercel rewrites `/api/*` to your Render backend.
- In local dev, Vite proxy forwards `/api/*` to `http://localhost:8000`.

You can also set `VITE_API_URL` in Vercel if you prefer absolute API URLs.

## Testing

1. Open your Vercel URL.
2. Check app pages and API-backed views.
3. If requests fail, inspect browser network and Render logs.

## Troubleshooting

### API calls return 404 or fail

- Verify rewrite destination in `vercel.json`.
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
