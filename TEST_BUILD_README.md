# Test and Build Scripts

This directory contains scripts to run tests and build both the backend and frontend components of the Writer Assistant application.

## Available Scripts

### 1. PowerShell Script (Recommended for Windows)
**File:** `test-and-build.ps1`

**Usage:**
```powershell
# Run from the project root directory
.\test-and-build.ps1
```

**Requirements:**
- PowerShell 5.1 or higher
- Python 3.10+ with venv
- Node.js 18+ with npm

### 2. Batch Script (Windows Command Prompt)
**File:** `test-and-build.bat`

**Usage:**
```cmd
REM Run from the project root directory
test-and-build.bat
```

**Requirements:**
- Windows Command Prompt
- Python 3.10+ with venv
- Node.js 18+ with npm

### 3. Bash Script (Git Bash/WSL/Linux/Mac)
**File:** `test-and-build.sh`

**Usage:**
```bash
# Make the script executable (first time only)
chmod +x test-and-build.sh

# Run from the project root directory
./test-and-build.sh
```

**Requirements:**
- Bash shell
- Python 3.10+ with venv
- Node.js 18+ with npm

## What the Scripts Do

### Backend Tests
1. **Virtual Environment Setup**
   - Checks if `backend/venv` exists
   - Creates and activates virtual environment if needed
   - Installs dependencies from `requirements.txt`

2. **Run Tests**
   - Executes pytest with verbose output
   - Generates code coverage reports (terminal and HTML)
   - Runs all tests in `backend/tests/`

3. **Coverage Report**
   - Terminal output shows coverage percentages
   - HTML report generated at `backend/htmlcov/index.html`

### Frontend Build and Test

1. **Dependency Check**
   - Checks if `frontend/node_modules` exists
   - Runs `npm install` if needed

2. **Linting**
   - Runs ESLint on the Angular codebase
   - Output saved to `frontend/frontend-lint.log`

3. **Unit Tests**
   - Runs Karma/Jasmine tests in headless Chrome
   - Generates code coverage report
   - Output saved to `frontend/frontend-test.log`

4. **Production Build**
   - Compiles Angular application for production
   - Optimizes and minifies code
   - Output saved to `frontend/dist/`
   - Build log saved to `frontend/frontend-build.log`

## Output Files

After running the script, you'll find:

### Backend
- `backend/htmlcov/index.html` - HTML coverage report
- `.coverage` - Coverage data file

### Frontend
- `frontend/dist/` - Production build output
- `frontend/frontend-lint.log` - Linting results
- `frontend/frontend-test.log` - Test results
- `frontend/frontend-build.log` - Build output

## Exit Codes

- `0` - All tests passed and build successful
- `1` - Tests failed or build error occurred

## Troubleshooting

### PowerShell Execution Policy Error

If you get an error about execution policy when running the PowerShell script:

```powershell
# Run this command to allow script execution (one time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

Ensure Python is installed and in your PATH:
```bash
python --version  # Should show Python 3.10 or higher
```

### Node/npm Not Found

Ensure Node.js is installed and in your PATH:
```bash
node --version   # Should show v18 or higher
npm --version    # Should show npm version
```

### Virtual Environment Issues

If the virtual environment has issues:
```bash
# Delete and recreate
rm -rf backend/venv  # or rmdir /s backend\venv on Windows
python -m venv backend/venv
```

### Node Modules Issues

If npm install fails or node_modules is corrupted:
```bash
# Delete and reinstall
rm -rf frontend/node_modules  # or rmdir /s frontend\node_modules on Windows
cd frontend
npm install
```

## Continuous Integration

These scripts are designed to be CI-friendly and can be integrated into:
- GitHub Actions
- GitLab CI/CD
- Jenkins
- Azure DevOps
- Any CI/CD system supporting shell scripts

### Example GitHub Actions Workflow

```yaml
name: Test and Build

on: [push, pull_request]

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Run tests and build
        run: ./test-and-build.sh
```

## Development Tips

### Running Only Backend Tests
```bash
cd backend
source venv/Scripts/activate  # Windows Git Bash
# or
. venv/bin/activate  # Linux/Mac
pytest tests/ -v
```

### Running Only Frontend Build
```bash
cd frontend
npm run build
```

### Watching Frontend Tests During Development
```bash
cd frontend
npm run test  # This will watch for changes
```

## Script Customization

You can modify the scripts to:
- Skip linting by commenting out the linting section
- Add additional test flags (e.g., `--maxfail=1` for pytest)
- Change coverage thresholds
- Add pre-commit hooks
- Include additional build steps

## Contact

For issues or questions about these scripts, please refer to the main project README or create an issue in the project repository.
