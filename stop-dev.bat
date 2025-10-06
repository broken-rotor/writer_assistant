@echo off
echo Stopping Writer Assistant Development Servers...
echo.

:: Kill Angular development server
echo Stopping Angular development server...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":4200"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Kill Python backend server
echo Stopping Python backend server...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Kill any remaining Node.js processes that might be running Angular
echo Cleaning up any remaining Node.js processes...
taskkill /f /im node.exe >nul 2>&1

:: Kill any remaining Python processes that might be running uvicorn
echo Cleaning up any remaining Python processes...
taskkill /f /im python.exe >nul 2>&1

echo.
echo Writer Assistant development servers have been stopped.
echo.
pause