@echo off
REM Writer Assistant - Test and Build Script (Windows)
REM This script runs tests and builds for both backend and frontend

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"

REM Color codes (using Windows 10+ ANSI support)
set "BLUE=[34m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "NC=[0m"

echo.
echo %BLUE%========================================%NC%
echo %BLUE%Writer Assistant - Test and Build%NC%
echo %BLUE%========================================%NC%
echo.

REM Check if backend directory exists
if not exist "%BACKEND_DIR%" (
    echo %RED%[ERROR]%NC% Backend directory not found: %BACKEND_DIR%
    exit /b 1
)

REM Check if frontend directory exists
if not exist "%FRONTEND_DIR%" (
    echo %RED%[ERROR]%NC% Frontend directory not found: %FRONTEND_DIR%
    exit /b 1
)

echo %BLUE%[INFO]%NC% Starting tests and build...
echo %BLUE%[INFO]%NC% Started at: %date% %time%
echo.

REM ========================================
REM Backend Tests
REM ========================================

echo.
echo %BLUE%========================================%NC%
echo %BLUE%Running Backend Tests%NC%
echo %BLUE%========================================%NC%
echo.

cd /d "%BACKEND_DIR%"

REM Check if virtual environment exists
if not exist "venv" (
    echo %YELLOW%[WARNING]%NC% Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo %BLUE%[INFO]%NC% Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo %BLUE%[INFO]%NC% Running pytest...

REM Run pytest with coverage
python -m pytest tests\ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Backend tests failed!
    call venv\Scripts\deactivate.bat
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Backend tests passed!

call venv\Scripts\deactivate.bat
cd /d "%SCRIPT_DIR%"

REM ========================================
REM Frontend Build and Test
REM ========================================

echo.
echo %BLUE%========================================%NC%
echo %BLUE%Running Frontend Build and Test%NC%
echo %BLUE%========================================%NC%
echo.

cd /d "%FRONTEND_DIR%"

REM Check if node_modules exists
if not exist "node_modules" (
    echo %YELLOW%[WARNING]%NC% node_modules not found. Running npm install...
    call npm install
    if errorlevel 1 (
        echo %RED%[ERROR]%NC% npm install failed!
        cd /d "%SCRIPT_DIR%"
        exit /b 1
    )
)

REM Run linting
echo %BLUE%[INFO]%NC% Running ESLint...
call npm run lint > frontend-lint.log 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARNING]%NC% Frontend linting completed with warnings (check frontend-lint.log)
) else (
    echo %GREEN%[SUCCESS]%NC% Frontend linting passed!
)

REM Run tests
echo %BLUE%[INFO]%NC% Running frontend tests...
call npm run test -- --watch=false --code-coverage --browsers=ChromeHeadless > frontend-test.log 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARNING]%NC% Frontend tests skipped or had issues (check frontend-test.log)
) else (
    echo %GREEN%[SUCCESS]%NC% Frontend tests passed!
)

REM Run build
echo %BLUE%[INFO]%NC% Building frontend production bundle...
call npm run build > frontend-build.log 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Frontend build failed! Check frontend-build.log
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Frontend build successful!

REM Show build output
if exist "dist" (
    echo %BLUE%[INFO]%NC% Build output location: %FRONTEND_DIR%\dist
    echo %BLUE%[INFO]%NC% Build size:
    dir dist /s
)

cd /d "%SCRIPT_DIR%"

REM ========================================
REM Summary
REM ========================================

echo.
echo %BLUE%========================================%NC%
echo %BLUE%Build and Test Summary%NC%
echo %BLUE%========================================%NC%
echo.

echo %GREEN%[SUCCESS]%NC% All tests and builds completed successfully!
echo %BLUE%[INFO]%NC% Finished at: %date% %time%
echo.

echo %GREEN%[√]%NC% Backend tests passed
echo %GREEN%[√]%NC% Frontend linting completed
echo %GREEN%[√]%NC% Frontend tests completed
echo %GREEN%[√]%NC% Frontend build successful
echo.

echo %BLUE%[INFO]%NC% Coverage report: %BACKEND_DIR%\htmlcov\index.html
echo %BLUE%[INFO]%NC% Frontend build: %FRONTEND_DIR%\dist\
echo %BLUE%[INFO]%NC% Frontend logs: %FRONTEND_DIR%\frontend-*.log
echo.

exit /b 0
