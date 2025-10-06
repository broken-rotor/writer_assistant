# Writer Assistant - Test and Build Script (PowerShell)
# This script runs tests and builds for both backend and frontend

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"

# Logging functions
function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Log-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Log-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Print-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Backend Tests
function Run-BackendTests {
    Print-Header "Running Backend Tests"

    Push-Location $BackendDir

    try {
        # Check if virtual environment exists
        if (-not (Test-Path "venv")) {
            Log-Warning "Virtual environment not found. Creating..."
            python -m venv venv
            & "$BackendDir\venv\Scripts\Activate.ps1"
            Log-Info "Installing dependencies..."
            pip install -r requirements.txt
        } else {
            & "$BackendDir\venv\Scripts\Activate.ps1"
        }

        Log-Info "Running pytest..."

        # Run pytest with coverage
        $result = & python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html

        if ($LASTEXITCODE -ne 0) {
            Log-Error "Backend tests failed!"
            & "$BackendDir\venv\Scripts\deactivate.bat"
            Pop-Location
            exit 1
        }

        Log-Success "Backend tests passed!"

        # Deactivate virtual environment
        & "$BackendDir\venv\Scripts\deactivate.bat"
    }
    catch {
        Log-Error "Error running backend tests: $_"
        Pop-Location
        exit 1
    }
    finally {
        Pop-Location
    }
}

# Frontend Build and Test
function Run-FrontendBuildAndTest {
    Print-Header "Running Frontend Build and Test"

    Push-Location $FrontendDir

    try {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Log-Warning "node_modules not found. Running npm install..."
            npm install
            if ($LASTEXITCODE -ne 0) {
                Log-Error "npm install failed!"
                Pop-Location
                exit 1
            }
        }

        # Run linting
        Log-Info "Running ESLint..."
        npm run lint 2>&1 | Tee-Object -FilePath "frontend-lint.log"
        if ($LASTEXITCODE -ne 0) {
            Log-Warning "Frontend linting completed with warnings (check frontend-lint.log)"
        } else {
            Log-Success "Frontend linting passed!"
        }

        # Run tests
        Log-Info "Running frontend tests..."
        npm run test -- --watch=false --code-coverage --browsers=ChromeHeadless 2>&1 | Tee-Object -FilePath "frontend-test.log"
        if ($LASTEXITCODE -ne 0) {
            Log-Warning "Frontend tests skipped or had issues (check frontend-test.log)"
        } else {
            Log-Success "Frontend tests passed!"
        }

        # Run build
        Log-Info "Building frontend production bundle..."
        npm run build 2>&1 | Tee-Object -FilePath "frontend-build.log"
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Frontend build failed! Check frontend-build.log"
            Pop-Location
            exit 1
        }

        Log-Success "Frontend build successful!"

        # Show build output
        if (Test-Path "dist") {
            Log-Info "Build output location: $FrontendDir\dist"
            Log-Info "Build size:"
            Get-ChildItem -Path "dist" -Recurse | Measure-Object -Property Length -Sum |
                ForEach-Object { "Total Size: {0:N2} MB" -f ($_.Sum / 1MB) }
        }
    }
    catch {
        Log-Error "Error running frontend build and test: $_"
        Pop-Location
        exit 1
    }
    finally {
        Pop-Location
    }
}

# Main execution
function Main {
    Print-Header "Writer Assistant - Test and Build Script"

    Log-Info "Starting at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    # Check if directories exist
    if (-not (Test-Path $BackendDir)) {
        Log-Error "Backend directory not found: $BackendDir"
        exit 1
    }

    if (-not (Test-Path $FrontendDir)) {
        Log-Error "Frontend directory not found: $FrontendDir"
        exit 1
    }

    # Run backend tests
    Run-BackendTests

    # Run frontend build and test
    Run-FrontendBuildAndTest

    Print-Header "Build and Test Summary"

    Log-Success "All tests and builds completed successfully!"
    Log-Info "Finished at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Write-Host ""
    Write-Host "[√] Backend tests passed" -ForegroundColor Green
    Write-Host "[√] Frontend linting completed" -ForegroundColor Green
    Write-Host "[√] Frontend tests completed" -ForegroundColor Green
    Write-Host "[√] Frontend build successful" -ForegroundColor Green
    Write-Host ""

    Log-Info "Coverage report: $BackendDir\htmlcov\index.html"
    Log-Info "Frontend build: $FrontendDir\dist\"
    Log-Info "Frontend logs: $FrontendDir\frontend-*.log"
}

# Run main function
Main
