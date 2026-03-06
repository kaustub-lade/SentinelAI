@echo off
title SentinelAI - Full Stack Launcher

echo.
echo  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗      █████╗ ██╗
echo  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     ██╔══██╗██║
echo  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     ███████║██║
echo  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     ██╔══██║██║
echo  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗██║  ██║██║
echo  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝
echo.
echo                  🛡️  Autonomous Cyber Defense Platform  🛡️
echo.
echo ================================================================================
echo.

echo This will start both backend and frontend servers in separate windows.
echo.
echo Backend (FastAPI):  http://localhost:8000
echo Frontend (React):   http://localhost:5173
echo API Docs:           http://localhost:8000/docs
echo.
echo Press any key to continue...
pause > nul

echo.
echo Starting Backend Server...
start "SentinelAI Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && if not exist .env copy .env.example .env && uvicorn app.main:app --reload"

timeout /t 5 /nobreak > nul

echo Starting Frontend Server...
start "SentinelAI Frontend" cmd /k "cd frontend && npm install && if not exist .env copy .env.example .env && npm run dev"

echo.
echo ================================================================================
echo.
echo  ✅ Both servers are starting in separate windows
echo.
echo  📍 Once servers are ready:
echo     1. Open http://localhost:5173 in your browser
echo     2. Login with any email/password (demo mode)
echo     3. Explore all features!
echo.
echo  📚 For detailed instructions, see QUICKSTART.md
echo.
echo  To stop servers: Close the terminal windows or press Ctrl+C in each
echo.
echo ================================================================================
echo.

pause
