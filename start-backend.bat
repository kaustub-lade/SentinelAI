@echo off
echo ====================================
echo  SentinelAI - Starting Backend
echo ====================================
echo.

cd backend

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Checking if virtual environment exists...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Checking for .env file...
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit backend/.env file with your API keys if needed
)

echo.
echo ====================================
echo  Starting FastAPI Server
echo ====================================
echo.
echo Backend will be available at: http://localhost:8000
echo API Documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload

pause
