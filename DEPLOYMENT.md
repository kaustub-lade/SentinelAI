# SentinelAI Deployment Guide (Secure Production)

This guide deploys SentinelAI with:

- Frontend on Vercel: https://sentinel-ai-flame.vercel.app
- Backend on Render: https://sentinelai-3glx.onrender.com
- MongoDB Atlas for persistent storage

## Prerequisites

- GitHub repository with this project pushed
- Render account
- Vercel account
- MongoDB Atlas URI and database name
- Strong production SECRET_KEY (32+ characters)

## Step 1: Configure Backend Service (Render)

1. Create/update the web service with [render.yaml](render.yaml).
2. Set environment variables in Render:
   - `MONGODB_URL` = Atlas URI
   - `MONGODB_DB_NAME` = `sentinelai`
   - `SECRET_KEY` = random secure key (32+ chars)
   - `ALLOWED_ORIGINS` = `https://sentinel-ai-flame.vercel.app`
   - Optional: `OPENAI_API_KEY`, `VIRUSTOTAL_API_KEY`, `NVD_API_KEY`
3. Confirm startup command:
   - `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Step 2: Configure Frontend (Vercel)

1. Import repository in Vercel.
2. Use `frontend` as the app root.
3. Set frontend env variable:
   - `VITE_API_URL=https://sentinelai-3glx.onrender.com`
4. Deploy.

## Step 3: Run Production Smoke Checks

Run after every backend deploy:

```bash
python backend/scripts/prod_smoke_check.py --backend-url https://sentinelai-3glx.onrender.com
```

Expected outcome:

- Health endpoint passes
- Register/login/me pass
- Vulnerability stats pass
- Phishing URL check passes
- Assistant chat passes

## Step 4: Security Rotation Routine

After any credential exposure or every scheduled rotation window:

1. Rotate MongoDB Atlas DB user password.
2. Update Render `MONGODB_URL` with new credentials.
3. Trigger backend redeploy.
4. Re-run smoke checks.

## Production Policy

- No localhost origins in production.
- No default SECRET_KEY.
- Startup fails fast when production env validation fails.

## Troubleshooting

### API calls return 404 or fail

- Confirm frontend `VITE_API_URL` points to Render backend.
- Confirm backend route prefix is `/api/v1`.

### CORS blocked

- Confirm `ALLOWED_ORIGINS=https://sentinel-ai-flame.vercel.app`.
- Do not include trailing slash.

### Backend cold starts

- Render free tier may sleep and take 30-60 seconds on first request.

## Production Recommendations

1. Keep MongoDB Atlas credentials rotated.
2. Add monitoring and error tracking.
3. Add CI gate to run smoke checks automatically.
4. Use paid tiers for predictable performance.
