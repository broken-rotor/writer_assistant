#!/bin/bash

# Writer Assistant - Test and Build Script
# This script runs tests and builds for both backend and frontend

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check if running on Windows (Git Bash/MINGW)
is_windows() {
    [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]
}

# Activate Python virtual environment
activate_venv() {
    if is_windows; then
        source "$BACKEND_DIR/venv/Scripts/activate"
    else
        source "$BACKEND_DIR/venv/bin/activate"
    fi
}

# Backend Tests
run_backend_tests() {
    print_header "Running Backend Tests"

    cd "$BACKEND_DIR"

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_warning "Virtual environment not found. Creating..."
        python -m venv venv
        activate_venv
        log_info "Installing dependencies..."
        pip install -r requirements.txt
    else
        activate_venv
    fi

    log_info "Running pytest..."

    # Run pytest with coverage
    if pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html; then
        log_success "Backend tests passed!"
        BACKEND_TESTS_STATUS="passed"
    else
        log_error "Backend tests failed!"
        BACKEND_TESTS_STATUS="failed"
        deactivate
        exit 1
    fi

    deactivate
    cd "$SCRIPT_DIR"
}

# Frontend Build and Test
run_frontend_build_and_test() {
    print_header "Running Frontend Build and Test"

    cd "$FRONTEND_DIR"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_warning "node_modules not found. Running npm install..."
        npm install
    fi

    # Run linting
    log_info "Running ESLint..."
    if npm run lint 2>&1 | tee frontend-lint.log; then
        log_success "Frontend linting passed!"
        FRONTEND_LINT_STATUS="passed"
    else
        log_warning "Frontend linting completed with warnings (check frontend-lint.log)"
        FRONTEND_LINT_STATUS="warning"
    fi

    # Run tests (if test configuration exists)
    log_info "Running frontend tests..."
    if npm run test -- --watch=false --code-coverage --browsers=ChromeHeadless 2>&1 | tee frontend-test.log; then
        log_success "Frontend tests passed!"
        FRONTEND_TESTS_STATUS="passed"
    else
        log_warning "Frontend tests skipped or failed (check frontend-test.log)"
        FRONTEND_TESTS_STATUS="warning"
    fi

    # Run build
    log_info "Building frontend production bundle..."
    if npm run build 2>&1 | tee frontend-build.log; then
        log_success "Frontend build successful!"
        FRONTEND_BUILD_STATUS="passed"

        # Show build output size
        if [ -d "dist" ]; then
            log_info "Build output location: $FRONTEND_DIR/dist"
            log_info "Build size:"
            du -sh dist/* 2>/dev/null || ls -lh dist/
        fi
    else
        log_error "Frontend build failed!"
        FRONTEND_BUILD_STATUS="failed"
        cd "$SCRIPT_DIR"
        exit 1
    fi

    cd "$SCRIPT_DIR"
}

# Main execution
main() {
    print_header "Writer Assistant - Test and Build Script"

    log_info "Starting at: $(date)"

    # Initialize status variables
    BACKEND_TESTS_STATUS="not_run"
    FRONTEND_LINT_STATUS="not_run"
    FRONTEND_TESTS_STATUS="not_run"
    FRONTEND_BUILD_STATUS="not_run"

    # Check if directories exist
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        exit 1
    fi

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        exit 1
    fi

    # Run backend tests
    run_backend_tests

    # Run frontend build and test
    run_frontend_build_and_test

    print_header "Build and Test Summary"

    log_info "Finished at: $(date)"

    echo ""
    # Backend tests
    if [ "$BACKEND_TESTS_STATUS" == "passed" ]; then
        echo -e "${GREEN}✓${NC} Backend tests passed"
    elif [ "$BACKEND_TESTS_STATUS" == "failed" ]; then
        echo -e "${RED}✗${NC} Backend tests failed"
    else
        echo -e "${YELLOW}⚠${NC} Backend tests not run"
    fi

    # Frontend linting
    if [ "$FRONTEND_LINT_STATUS" == "passed" ]; then
        echo -e "${GREEN}✓${NC} Frontend linting passed"
    elif [ "$FRONTEND_LINT_STATUS" == "warning" ]; then
        echo -e "${YELLOW}⚠${NC} Frontend linting completed with warnings"
    else
        echo -e "${YELLOW}⚠${NC} Frontend linting not run"
    fi

    # Frontend tests
    if [ "$FRONTEND_TESTS_STATUS" == "passed" ]; then
        echo -e "${GREEN}✓${NC} Frontend tests passed"
    elif [ "$FRONTEND_TESTS_STATUS" == "warning" ]; then
        echo -e "${YELLOW}⚠${NC} Frontend tests completed with warnings or skipped"
    else
        echo -e "${YELLOW}⚠${NC} Frontend tests not run"
    fi

    # Frontend build
    if [ "$FRONTEND_BUILD_STATUS" == "passed" ]; then
        echo -e "${GREEN}✓${NC} Frontend build successful"
    elif [ "$FRONTEND_BUILD_STATUS" == "failed" ]; then
        echo -e "${RED}✗${NC} Frontend build failed"
    else
        echo -e "${YELLOW}⚠${NC} Frontend build not run"
    fi
    echo ""

    # Overall status
    if [ "$BACKEND_TESTS_STATUS" == "passed" ] && [ "$FRONTEND_BUILD_STATUS" == "passed" ]; then
        log_success "All critical tests and builds completed successfully!"
    else
        log_warning "Some components failed or completed with warnings. Check logs above."
    fi

    log_info "Coverage report: $BACKEND_DIR/htmlcov/index.html"
    log_info "Frontend build: $FRONTEND_DIR/dist/"
    log_info "Frontend logs: $FRONTEND_DIR/frontend-*.log"
}

# Run main function
main "$@"
