# SentinelAI

SentinelAI is an AI-powered cybersecurity platform for threat detection, phishing analysis, vulnerability prioritization, and a security assistant UI.

## Live URLs

- Frontend: https://sentinel-ai-flame.vercel.app
- Backend API: https://sentinelai-3glx.onrender.com
- API Docs: https://sentinelai-3glx.onrender.com/docs

## Features

- Malware analysis with static features, YARA hooks, and model scaffolding
- Phishing detection with heuristic + ML scaffolding
- Vulnerability intelligence and CVE prioritization
- AI security assistant
- JWT auth with refresh tokens and role checks
- Rate limiting and audit logging
- MITRE ATT&CK mapping scaffolding

## Architecture

- Frontend: React + Vite + Tailwind
- Backend: FastAPI + Python
- Data: MongoDB Atlas
- Task queue: Celery + Redis

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `backend/.env` with your backend settings if needed.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `frontend/.env`:

```env
VITE_API_URL=https://sentinelai-3glx.onrender.com
```

## Local Development

If you want to run the full stack together, use the provided scripts or Docker Compose. The local development tools still bind to your machine during development, but the production deployment URLs above are the ones to use in the browser.

## Deployment Notes

- Ensure MongoDB credentials are correct and URL-encoded if they contain special characters.
- Ensure `ALLOWED_ORIGINS` includes the Vercel frontend URL.
- Render should deploy from `main`.

## Support

See `QUICKSTART.md` for a step-by-step run guide and `docs/manual_tasks.md` for manual setup tasks.
