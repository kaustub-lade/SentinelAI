# Quick Start - Deploy to Vercel and Render

Your SentinelAI project is configured for Vercel experimental services for the frontend and backend.

## What Was Added

- `vercel.json` for Vercel experimental services
- `render.yaml` for backend deployment on Render
- Updated deployment docs for Vercel flow

## Next Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Migrate deployment setup to Vercel and Render"
git push origin main
```

### 2. Deploy Backend Service

1. In Vercel, keep the `backend` service entrypoint in [vercel.json](vercel.json).
2. Set backend environment variables in Vercel if needed:
   - `OPENAI_API_KEY`
   - `VIRUSTOTAL_API_KEY`
   - `SECRET_KEY`
   - `ALLOWED_ORIGINS`
3. Make sure the backend service is deployed from the `backend` folder.

### 3. Deploy Frontend on Vercel

1. Open [vercel.json](vercel.json) and confirm the frontend and backend services match your repo layout.
2. Commit and push the change.
3. Go to https://vercel.com and import your GitHub repository.
4. Deploy using the defaults from [vercel.json](vercel.json).
5. Copy your Vercel URL.

### 4. Update CORS on Render

Set `ALLOWED_ORIGINS` in Vercel to include your production frontend domain if your backend enforces CORS:

```text
https://your-project.vercel.app,http://localhost:5173
```

## Done

Visit your Vercel URL and test the app.

## If API Calls Fail

- Check [vercel.json](vercel.json) service entrypoints and route prefixes
- Check backend environment variable `ALLOWED_ORIGINS` includes your Vercel URL
- Check backend logs for errors
