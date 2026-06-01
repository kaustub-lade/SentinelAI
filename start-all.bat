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
echo Backend (FastAPI):  starting in a separate window
echo Frontend (React):   starting in a separate window
echo API Docs:           available from the backend service once it starts
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
echo     1. Open the frontend URL shown by the Vite server in your browser
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
