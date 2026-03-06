# 🚀 SentinelAI - Quick Start Guide

## Prerequisites

Before you begin, make sure you have:

- **Node.js 18+** and npm installed
- **Python 3.11+** installed
- **Git** (optional, for version control)

## Step-by-Step Setup

### 1. Backend Setup (FastAPI)

Navigate to the backend directory:

```bash
cd SentinelAI/backend
```

Create a Python virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
# Copy the example env file
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
```

Edit `.env` file (optional - works without API keys for demo):

```env
OPENAI_API_KEY=your_key_here  # Optional
VIRUSTOTAL_API_KEY=your_key_here  # Optional
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

**Backend should now be running at:** `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

### 2. Frontend Setup (React + Vite)

Open a **new terminal** window and navigate to frontend:

```bash
cd SentinelAI/frontend
```

Install Node.js dependencies:

```bash
npm install
```

Create environment file:

```bash
# Copy the example env file
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
```

The `.env` file should contain:

```env
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

**Frontend should now be running at:** `http://localhost:5173`

---

### 3. Access the Application

1. Open your browser and go to: **http://localhost:5173**
2. You'll see the login page
3. **Login with any email/password** (demo mode - authentication is mocked)
4. Explore the features:
   - **Dashboard** - Threat overview and analytics
   - **Malware Analysis** - Upload files for analysis
   - **Phishing Detection** - Analyze suspicious emails
   - **Vulnerability Intelligence** - CVE prioritization
   - **AI Assistant** - Ask security questions

---

## Quick Test Scenarios

### Test Malware Detection
1. Go to "Malware Analysis"
2. Upload any file (e.g., a .txt or .exe file)
3. Click "Analyze File"
4. View the AI-powered results

### Test Phishing Detection
1. Go to "Phishing Detection"
2. Paste a suspicious email:
```
From: support@paypa1.com
Subject: Urgent: Verify your account immediately

Dear User,
Your account has been suspended. Click here to verify immediately:
http://suspicious-link.tk/verify
```
3. Click "Analyze Email"
4. View phishing indicators

### Test AI Assistant
1. Go to "AI Assistant"
2. Ask questions like:
   - "What are my critical vulnerabilities?"
   - "Show me today's threat summary"
   - "How do I detect phishing?"

---

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Change port in command
uvicorn app.main:app --reload --port 8001
```

**Module not found errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

**Port 5173 already in use:**
```bash
# Kill the process or change port in vite.config.js
npm run dev -- --port 3000
```

**API connection errors:**
- Make sure backend is running on port 8000
- Check `.env` file has correct `VITE_API_URL`

**Module not found:**
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

---

## Project Structure

```
SentinelAI/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration
│   │   └── main.py       # Entry point
│   ├── requirements.txt
│   └── .env
│
├── frontend/             # React frontend
│   ├── src/
│   │   ├── pages/       # UI pages
│   │   ├── components/  # Reusable components
│   │   ├── services/    # API calls
│   │   └── App.jsx      # Main app
│   ├── package.json
│   └── .env
│
└── README.md
```

---

## Development Tips

### Backend Hot Reload
FastAPI automatically reloads when you change Python files (with `--reload` flag)

### Frontend Hot Reload
Vite automatically reloads when you change React files

### API Testing
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### Adding New Features
1. **Backend**: Add endpoints in `backend/app/api/v1/endpoints/`
2. **Frontend**: Add pages in `frontend/src/pages/`
3. **API Integration**: Update `frontend/src/services/api.js`

---

## Next Steps

- ✅ Add real ML models for malware detection
- ✅ Integrate OpenAI API for better AI assistant
- ✅ Connect VirusTotal API for threat intelligence
- ✅ Add user authentication with JWT
- ✅ Deploy to cloud (AWS/Azure/GCP)

---

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review API docs at `/docs`
- Check browser console for errors

**Happy Hacking! 🛡️**
