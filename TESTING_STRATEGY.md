# Writer Assistant Testing Strategy

## Complete Testing Approach

```
┌────────────────────────────────────────────────────────────────────┐
│                        Testing Pyramid                              │
└────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Manual     │  ← User acceptance testing
                    │     E2E      │
                    └──────────────┘
                   /                \
                  /                  \
           ┌─────────────┐    ┌──────────────┐
           │ Integration │    │  Smoke Tests │  ← test_integration.py
           │    Tests    │    │   (Deploy)   │     (After deployment)
           └─────────────┘    └──────────────┘
          /                                    \
         /                                      \
  ┌────────────┐                          ┌──────────────┐
  │   Unit     │                          │   Static     │  ← test-and-build.*
  │   Tests    │                          │  Analysis    │     (Before commit)
  └────────────┘                          └──────────────┘

  ↑ Most tests                                 Fast feedback ↑
  ↑ Fastest execution                          Broad coverage ↑
```

## Two-Script Strategy

### Script 1: test-and-build.* (Development & CI/CD)

**Purpose:** Validate code quality BEFORE deployment

```
┌─────────────────────────────────────────────────────┐
│          test-and-build.sh/ps1/bat                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Backend Tests                                      │
│  ├── Unit tests (pytest)                           │
│  ├── Code coverage (>80% target)                   │
│  └── HTML report generation                        │
│                                                     │
│  Frontend Tests                                     │
│  ├── Linting (ESLint)                              │
│  ├── Unit tests (Karma/Jasmine)                    │
│  ├── TypeScript compilation                        │
│  └── Production build                              │
│                                                     │
│  Output:                                            │
│  ├── backend/htmlcov/index.html                    │
│  ├── frontend/dist/                                │
│  └── frontend/*.log files                          │
│                                                     │
└─────────────────────────────────────────────────────┘

When to run:
  • During development (./quick-test.sh for speed)
  • Before git commit
  • In CI/CD pipeline (every push)
  • Before creating pull request

Time: ~1-3 minutes
Dependencies: Python venv, Node.js (created automatically)
Services required: NONE
```

### Script 2: test_integration.py (Deployment Validation)

**Purpose:** Validate services AFTER deployment

```
┌─────────────────────────────────────────────────────┐
│            test_integration.py                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Service Health Checks                              │
│  ├── Backend running? (GET /health)                │
│  ├── Frontend accessible? (GET /)                  │
│  └── API responding? (GET /api/v1/...)             │
│                                                     │
│  API Contract Tests                                 │
│  ├── Outline generation endpoint                   │
│  ├── Chapter generation endpoint                   │
│  └── Response format validation                    │
│                                                     │
│  Architecture Validation                            │
│  ├── Angular app structure                         │
│  ├── Client-side storage                           │
│  └── Backend/Frontend communication                │
│                                                     │
│  Output:                                            │
│  └── Console: PASS/FAIL for each check             │
│                                                     │
└─────────────────────────────────────────────────────┘

When to run:
  • After starting local services
  • After deploying to staging
  • After deploying to production
  • Periodic health monitoring

Time: ~10-30 seconds
Dependencies: requests library
Services required: Backend + Frontend MUST be running
```

## Development Workflow

### Day-to-Day Development

```bash
# 1. Start coding
vim backend/app/services/writer_agent.py

# 2. Quick test (fast feedback)
./quick-test.sh backend           # ~10 seconds

# 3. Continue coding
vim frontend/src/app/features/story-list/story-list.component.ts

# 4. Quick test again
./quick-test.sh frontend          # ~15 seconds

# 5. Before committing, run full suite
./test-and-build.sh               # ~2 minutes

# 6. Commit if tests pass
git add .
git commit -m "Add feature X"
git push
```

### Pre-Deployment Checklist

```bash
# 1. Run unit tests and build
./test-and-build.sh
✓ All unit tests pass
✓ Code coverage > 80%
✓ Linting passes
✓ Production build created

# 2. Start services locally
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
cd frontend && ng serve &

# 3. Run integration tests
python test_integration.py
✓ Backend health OK
✓ Frontend accessible
✓ API endpoints responding

# 4. Deploy to staging
./deploy.sh staging

# 5. Smoke test staging
python test_integration.py  # (against staging URL)
✓ All checks pass

# 6. Deploy to production
./deploy.sh production

# 7. Smoke test production
python test_integration.py  # (against production URL)
✓ All checks pass
```

## CI/CD Pipeline Integration

### GitHub Actions Example

```yaml
name: Test and Deploy

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # Step 1: Unit tests and build
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Run unit tests and build
        run: ./test-and-build.sh

      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: backend/htmlcov/

      - name: Upload frontend build
        uses: actions/upload-artifact@v3
        with:
          name: frontend-build
          path: frontend/dist/

  # Step 2: Deploy to staging (only on main branch)
  deploy-staging:
    needs: test-and-build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: ./deploy.sh staging

      - name: Wait for deployment
        run: sleep 30

      - name: Run integration tests
        run: |
          export BACKEND_URL=https://staging-api.example.com
          export FRONTEND_URL=https://staging.example.com
          python test_integration.py

  # Step 3: Deploy to production (manual approval)
  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - name: Deploy to production
        run: ./deploy.sh production

      - name: Wait for deployment
        run: sleep 30

      - name: Run integration tests
        run: |
          export BACKEND_URL=https://api.example.com
          export FRONTEND_URL=https://app.example.com
          python test_integration.py

      - name: Notify team
        run: echo "Production deployment complete!"
```

## Test Coverage Goals

### Backend (Python)

| Component | Coverage Target | Current Script |
|-----------|----------------|----------------|
| Models | 90% | test-and-build.* |
| Services | 85% | test-and-build.* |
| API Endpoints | 80% | test-and-build.* |
| Agents | 75% | test-and-build.* |
| Workflows | 75% | test-and-build.* |
| **Overall** | **>80%** | **test-and-build.*** |

### Frontend (Angular)

| Component | Coverage Target | Current Script |
|-----------|----------------|----------------|
| Components | 70% | test-and-build.* |
| Services | 80% | test-and-build.* |
| Models | 90% | test-and-build.* |
| Pipes/Directives | 85% | test-and-build.* |
| **Overall** | **>75%** | **test-and-build.*** |

### Integration

| Test Area | Coverage | Current Script |
|-----------|----------|----------------|
| API Health | 100% | test_integration.py |
| Endpoint Availability | 100% | test_integration.py |
| Frontend Accessibility | 100% | test_integration.py |
| Architecture Validation | 100% | test_integration.py |

## Quick Reference Commands

### Development

```bash
# Fast feedback during coding
./quick-test.sh                    # Test both (20-30 sec)
./quick-test.sh backend            # Backend only (10 sec)
./quick-test.sh frontend           # Frontend only (15 sec)

# Full validation before commit
./test-and-build.sh                # All tests + build (1-3 min)

# PowerShell (Windows)
.\test-and-build.ps1

# Command Prompt (Windows)
test-and-build.bat
```

### Deployment Validation

```bash
# Start services first
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
cd frontend && ng serve &

# Then run integration tests
python test_integration.py         # Smoke test (10-30 sec)
```

### View Reports

```bash
# Backend coverage report
open backend/htmlcov/index.html    # Mac
start backend/htmlcov/index.html   # Windows
xdg-open backend/htmlcov/index.html # Linux

# Frontend build output
ls -lh frontend/dist/

# Test logs
cat frontend/frontend-test.log
cat frontend/frontend-lint.log
cat frontend/frontend-build.log
```

## What Each Script Catches

### test-and-build.* catches:

- ❌ Syntax errors
- ❌ Type errors
- ❌ Logic bugs in functions
- ❌ Broken imports
- ❌ Missing dependencies
- ❌ Linting violations
- ❌ Test failures
- ❌ Build failures
- ❌ Low code coverage

### test_integration.py catches:

- ❌ Services not running
- ❌ Port conflicts
- ❌ API contract violations
- ❌ Frontend/backend communication issues
- ❌ Deployment problems
- ❌ CORS issues
- ❌ Network connectivity
- ❌ Service health problems

## Best Practices

### Before Committing Code

```bash
# 1. Run full test suite
./test-and-build.sh

# 2. Check coverage didn't decrease
# View backend/htmlcov/index.html

# 3. Review build output
ls -lh frontend/dist/

# 4. Commit
git add .
git commit -m "Add feature X"
```

### Before Deploying

```bash
# 1. Ensure tests pass
./test-and-build.sh

# 2. Build Docker images
docker-compose build

# 3. Test locally with Docker
docker-compose up -d
python test_integration.py

# 4. Deploy to staging
./deploy.sh staging

# 5. Test staging
BACKEND_URL=https://staging-api.example.com python test_integration.py

# 6. Deploy to production
./deploy.sh production

# 7. Test production
BACKEND_URL=https://api.example.com python test_integration.py
```

## Summary

| Script | Purpose | When | Time | Services |
|--------|---------|------|------|----------|
| **test-and-build.\*** | Code quality validation | Before commit | 1-3 min | None |
| **quick-test.sh** | Fast development feedback | During coding | 10-30 sec | None |
| **test_integration.py** | Deployment validation | After deploy | 10-30 sec | Required |

**Use all three for complete coverage!** 🎯
