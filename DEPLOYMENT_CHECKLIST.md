# Quick Deployment Checklist

## Before You Start
- [ ] Code pushed to GitHub repository
- [ ] Have OpenAI API key (optional)
- [ ] Have VirusTotal API key (optional)
- [ ] Created Vercel account

## Part 1: Configure Backend Service

1. Deploy backend service in Vercel
   - [ ] Keep backend entrypoint set to `backend`
   - [ ] Confirm routePrefix is `/_/backend`

2. Set Environment Variables
   - [ ] `OPENAI_API_KEY` = your OpenAI key
   - [ ] `VIRUSTOTAL_API_KEY` = your VirusTotal key  
   - [ ] `SECRET_KEY` = (auto-generate or use a random 32-char string)
   - [ ] `ALLOWED_ORIGINS` = (set if your backend enforces CORS)

3. Wait for Deployment
   - [ ] Wait 5-10 minutes for build to complete
   - [ ] Test backend route: `/_/backend/docs`

## Part 2: Deploy Frontend on Vercel

1. Update Configuration
   - [ ] Edit [vercel.json](vercel.json)
   - [ ] Commit and push: `git add . && git commit -m "Update Render URL" && git push`

2. Deploy to Vercel
   - [ ] Go to https://vercel.com and log in
   - [ ] Click "Add New" → "Project"
   - [ ] Import your GitHub repository
   - [ ] Confirm project settings and deploy

3. Set Environment Variable
   - [ ] Optional: add `VITE_API_URL` = `/_/backend`
   - [ ] If not set, API traffic uses the default backend service prefix

4. Deploy
   - [ ] Click "Deploy"
   - [ ] Wait 3-5 minutes for build
   - [ ] Copy your Vercel URL: `https://your-project.vercel.app`

## Part 3: Final Configuration

1. Update Backend CORS
    - [ ] Update `ALLOWED_ORIGINS` with your Vercel URL if needed:
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
- **Backend**: ___________________________
- **API Docs**: /_/backend/docs

## Common Issues

**Backend won't start?**
- Check Vercel service logs for Python errors
- Verify requirements.txt is in backend/ folder
- Make sure Python 3.11+ is used

- **Frontend shows "Connection Error"?**
- Verify `vercel.json` has the correct service entrypoints
- If using env vars, verify VITE_API_URL is set in Vercel
- Ensure backend ALLOWED_ORIGINS includes Vercel URL if CORS is enforced

**CORS Errors?**
- Double-check ALLOWED_ORIGINS includes your Vercel URL
- Make sure there are no trailing slashes
- Wait a few minutes for backend to redeploy after changing env vars

- **Backend is slow/times out?**
- Vercel service cold starts can occur on first request
- First request after sleep takes 30-60 seconds (cold start)

## Optional: Custom Domain

### Vercel
1. Go to Project Settings → Domains
2. Click "Add"
3. Follow DNS setup instructions

## Need Help?

- Full guide: See DEPLOYMENT.md
- Render docs: https://render.com/docs
- Vercel docs: https://vercel.com/docs
