# Quick Start - Deploy to Vercel and Render

Your SentinelAI project is configured for Vercel (frontend) and Render (backend).

## What Was Added

- `vercel.json` for frontend deployment and API rewrites
- `render.yaml` for backend deployment on Render
- Updated deployment docs for Vercel flow

## Next Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Migrate deployment setup to Vercel and Render"
git push origin main
```

### 2. Deploy Backend on Render First

1. Go to https://render.com
2. Create a new Web Service from your repository
3. Use:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables:
   - `OPENAI_API_KEY`
   - `VIRUSTOTAL_API_KEY`
   - `SECRET_KEY`
   - `ALLOWED_ORIGINS` (set after Vercel URL is available)
5. Copy your Render backend URL

### 3. Deploy Frontend on Vercel

1. Open [frontend/vercel.json](frontend/vercel.json)
2. Replace `your-render-backend-url.onrender.com` with your actual Render URL
3. Commit and push the change
4. Go to https://vercel.com and import your GitHub repository
5. Set the Root Directory to `frontend`
6. Deploy using the defaults from [frontend/vercel.json](frontend/vercel.json)
7. Copy your Vercel URL

### 4. Update CORS on Render

Set `ALLOWED_ORIGINS` in Render to include your Vercel domain:

```text
https://your-project.vercel.app,http://localhost:5173
```

## Done

Visit your Vercel URL and test the app.

## If API Calls Fail

- Check `vercel.json` rewrite destination points to the correct Render backend
- Check Render environment variable `ALLOWED_ORIGINS` includes your Vercel URL
- Check Render logs for backend errors
