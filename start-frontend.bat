@echo off
echo ====================================
echo  SentinelAI - Starting Frontend
echo ====================================
echo.

cd frontend

echo Checking Node.js installation...
node --version
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Checking npm installation...
npm --version

echo.
echo Installing dependencies...
npm install

echo.
echo Checking for .env file...
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo.
echo ====================================
echo  Starting Vite Development Server
echo ====================================
echo.
echo Frontend will be available at: http://localhost:5173
echo.
echo Make sure backend is running on port 8000
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause
