# Quick Start - Deploy Frontend on Vercel and Backend on Render

SentinelAI is configured for:

- Frontend: Vercel
- Backend: Render (Docker)
- Database: MongoDB Atlas

## 1. Push Latest Code

Use your normal git flow:

git add .
git commit -m "Deploy-ready MongoDB config"
git push origin main

## 2. Deploy Backend on Render

1. In Render, create or update the backend web service using [render.yaml](render.yaml).
2. Ensure these backend environment variables are set in Render:
   - OPENAI_API_KEY
   - VIRUSTOTAL_API_KEY
   - SECRET_KEY
   - ALGORITHM=HS256
   - ACCESS_TOKEN_EXPIRE_MINUTES=30
   - MONGODB_URL
   - MONGODB_DB_NAME=sentinelai
   - ALLOWED_ORIGINS
3. Confirm Render uses [backend/Dockerfile](backend/Dockerfile) and the repo root as docker context.

## 3. Deploy Frontend on Vercel

1. Import the repository in Vercel.
2. Set the frontend root to the frontend app (if prompted).
3. Set frontend API base URL to your Render backend URL.
4. Deploy and copy your Vercel frontend URL.

## 4. Set CORS Correctly

Set backend ALLOWED_ORIGINS to include your deployed frontend URL and local dev URL.

Example:

https://your-frontend.vercel.app,http://localhost:5173

## 5. Smoke Test

Validate these flows in production:

- Register and login
- Vulnerability stats page
- Phishing URL check
- Assistant chat
- Admin report export

## If Something Fails

- Check Render logs first
- Verify MONGODB_URL and MONGODB_DB_NAME on Render
- Verify ALLOWED_ORIGINS includes the exact Vercel domain
- Verify frontend API base URL points to Render backend
