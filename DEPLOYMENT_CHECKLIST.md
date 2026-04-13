# Quick Deployment Checklist

## Before You Start
- [ ] Code pushed to GitHub repository
- [ ] Have MongoDB Atlas URI and DB name
- [ ] Have strong production SECRET_KEY (32+ chars)
- [ ] Created Render and Vercel accounts

## Part 1: Configure Backend Service (Render)

1. Deploy backend service in Render
   - [ ] Use [render.yaml](render.yaml)
   - [ ] Confirm Dockerfile path is `backend/Dockerfile`

2. Set Environment Variables
- [ ] `MONGODB_URL` = Atlas URI
- [ ] `MONGODB_DB_NAME` = `sentinelai`
- [ ] `SECRET_KEY` = random 32+ char secret
- [ ] `ALLOWED_ORIGINS` = `https://sentinel-ai-flame.vercel.app`
- [ ] `OPENAI_API_KEY` = optional
- [ ] `VIRUSTOTAL_API_KEY` = optional
- [ ] `NVD_API_KEY` = optional

3. Wait for Deployment
   - [ ] Wait for build to complete
   - [ ] Test backend route: `https://sentinelai-3glx.onrender.com/health`

## Part 2: Deploy Frontend (Vercel)

1. Update Configuration
   - [ ] Ensure `VITE_API_URL` points to `https://sentinelai-3glx.onrender.com`
   - [ ] Confirm frontend deploys from `frontend` folder

2. Deploy to Vercel
   - [ ] Go to https://vercel.com and log in
   - [ ] Click "Add New" → "Project"
   - [ ] Import your GitHub repository
   - [ ] Confirm project settings and deploy

3. Set Environment Variable
   - [ ] `VITE_API_URL` = `https://sentinelai-3glx.onrender.com`

4. Deploy
   - [ ] Click "Deploy"
   - [ ] Copy your Vercel URL: `https://sentinel-ai-flame.vercel.app`

## Part 3: Production Verification

1. Run automated backend smoke checks
   - [ ] Command:
     ```
     python backend/scripts/prod_smoke_check.py --backend-url https://sentinelai-3glx.onrender.com
     ```

2. Test Your Deployment
   - [ ] Visit frontend: `https://sentinel-ai-flame.vercel.app`
   - [ ] Log in and test key flows
   - [ ] Check Render logs if issues occur

## URLs to Save

- **Frontend (Vercel)**: https://sentinel-ai-flame.vercel.app
- **Backend (Render)**: https://sentinelai-3glx.onrender.com
- **API Docs**: https://sentinelai-3glx.onrender.com/docs

## Common Issues

**Backend won't start?**
- Check Render logs for startup validation errors
- Verify `MONGODB_URL`, `SECRET_KEY`, and `ALLOWED_ORIGINS` are set
- Confirm `ALLOWED_ORIGINS` does not include localhost

- **Frontend shows "Connection Error"?**
- Verify `VITE_API_URL` is `https://sentinelai-3glx.onrender.com`
- Check browser Network tab for failing API requests

**CORS Errors?**
- Ensure `ALLOWED_ORIGINS=https://sentinel-ai-flame.vercel.app`
- Remove trailing slash in origin value

- **Backend is slow/times out?**
- Render free tier can cold start on first request
- First request after sleep can take 30-60 seconds

## Optional: Custom Domain

### Vercel
1. Go to Project Settings → Domains
2. Click "Add"
3. Follow DNS setup instructions

## Need Help?

- Full guide: See DEPLOYMENT.md
- Render docs: https://render.com/docs
- Vercel docs: https://vercel.com/docs
