# Quick Deployment Checklist

## Before You Start
- [ ] Code pushed to GitHub repository
- [ ] Have OpenAI API key (optional)
- [ ] Have VirusTotal API key (optional)
- [ ] Created Render account
- [ ] Created Vercel account

## Part 1: Deploy Backend on Render (Do This First!)

1. Deploy to Render
   - [ ] Go to https://render.com and log in
   - [ ] Click "New +" → "Web Service"
   - [ ] Connect your GitHub repository
   - [ ] Use these settings:
     * Name: `sentinelai-backend`
     * Environment: `Python 3`
     * Build Command: `pip install -r backend/requirements.txt`
     * Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. Set Environment Variables in Render
   - [ ] `OPENAI_API_KEY` = your OpenAI key
   - [ ] `VIRUSTOTAL_API_KEY` = your VirusTotal key  
   - [ ] `SECRET_KEY` = (auto-generate or use a random 32-char string)
   - [ ] `ALLOWED_ORIGINS` = (leave blank for now, will update after frontend)
   - [ ] Click "Create Web Service"

3. Wait for Deployment
   - [ ] Wait 5-10 minutes for build to complete
   - [ ] Copy your backend URL: `https://sentinelai-backend-XXXX.onrender.com`
   - [ ] Test it: Visit `https://your-backend-url.onrender.com/docs`

## Part 2: Deploy Frontend on Vercel

1. Update Configuration
   - [ ] Edit [frontend/vercel.json](frontend/vercel.json)
   - [ ] Replace `your-render-backend-url.onrender.com` with your actual Render URL
   - [ ] Commit and push: `git add . && git commit -m "Update Render URL" && git push`

2. Deploy to Vercel
   - [ ] Go to https://vercel.com and log in
   - [ ] Click "Add New" → "Project"
   - [ ] Import your GitHub repository
   - [ ] Set Root Directory to `frontend`
   - [ ] Confirm project settings and deploy

3. Set Environment Variable
   - [ ] Optional: add `VITE_API_URL` = your Render backend URL
   - [ ] If not set, API traffic uses Vercel rewrite rules in [frontend/vercel.json](frontend/vercel.json)

4. Deploy
   - [ ] Click "Deploy"
   - [ ] Wait 3-5 minutes for build
   - [ ] Copy your Vercel URL: `https://your-project.vercel.app`

## Part 3: Final Configuration

1. Update Backend CORS
   - [ ] Go back to Render dashboard
   - [ ] Navigate to your service → Environment
   - [ ] Update `ALLOWED_ORIGINS` with your Vercel URL:
     ```
     https://your-project.vercel.app,http://localhost:5173
     ```
   - [ ] Save changes (backend will auto-redeploy)

2. Test Your Deployment
   - [ ] Visit your Vercel URL
   - [ ] Try to log in or use features
   - [ ] Check browser console for errors
   - [ ] Check Render logs if issues occur

## URLs to Save

- **Frontend (Vercel)**: ___________________________
- **Backend (Render)**: ___________________________
- **API Docs**: https://your-backend-url.onrender.com/docs

## Common Issues

**Backend won't start?**
- Check Render logs for Python errors
- Verify requirements.txt is in backend/ folder
- Make sure Python 3.11+ is used

**Frontend shows "Connection Error"?**
- Verify `vercel.json` has the correct Render URL in rewrites
- If using env vars, verify VITE_API_URL is set in Vercel
- Ensure backend ALLOWED_ORIGINS includes Vercel URL

**CORS Errors?**
- Double-check ALLOWED_ORIGINS in Render includes your Vercel URL
- Make sure there are no trailing slashes
- Wait a few minutes for backend to redeploy after changing env vars

**Backend is slow/times out?**
- Render free tier spins down after 15 min inactivity
- First request after sleep takes 30-60 seconds (cold start)
- Upgrade to paid tier for always-on service

## Optional: Custom Domain

### Vercel
1. Go to Project Settings → Domains
2. Click "Add"
3. Follow DNS setup instructions

### Render  
1. Go to your service → Settings
2. Click "Custom Domain"
3. Add your domain and update DNS

## Need Help?

- Full guide: See DEPLOYMENT.md
- Render docs: https://render.com/docs
- Vercel docs: https://vercel.com/docs
