@echo off
echo Starting Writer Assistant in Development Mode...
echo.

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

:: Start Frontend Development Server
echo Starting Angular Frontend Development Server...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo Error: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

start "Angular Dev Server" cmd /k "npx ng serve --open --port 4200"
echo Frontend server starting on http://localhost:4200

:: Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

:: Start Backend Development Server
echo Starting Python Backend Development Server...
cd /d "%~dp0backend"

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment and install dependencies
call venv\Scripts\activate.bat
if not exist "requirements.txt" (
    echo Warning: requirements.txt not found, creating basic requirements...
    echo fastapi==0.104.1> requirements.txt
    echo uvicorn[standard]==0.24.0>> requirements.txt
    echo python-multipart==0.0.6>> requirements.txt
    echo pydantic==1.10.12>> requirements.txt
    echo python-dotenv==1.0.0>> requirements.txt
)

venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install backend dependencies
    pause
    exit /b 1
)

start "Python Backend Server" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo Backend server starting on http://localhost:8000

echo.
echo ============================================
echo Writer Assistant Development Environment
echo ============================================
echo Frontend: http://localhost:4200
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Both servers are starting in separate windows.
echo Close those windows or press Ctrl+C in them to stop the servers.
echo.
pause