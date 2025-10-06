#!/bin/bash

echo "Starting Writer Assistant in Development Mode..."
echo

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed"
    echo "Please install Python from https://python.org/"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to cleanup on exit
cleanup() {
    echo
    echo "Shutting down Writer Assistant..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "Frontend server stopped"
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "Backend server stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Frontend Development Server
echo "Starting Angular Frontend Development Server..."
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install frontend dependencies"
        exit 1
    fi
fi

# Start frontend in background
npx ng serve --port 4200 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend server starting on http://localhost:4200 (PID: $FRONTEND_PID)"

# Wait a moment for frontend to start
sleep 3

# Start Backend Development Server
echo "Starting Python Backend Development Server..."
cd "$SCRIPT_DIR/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        kill $FRONTEND_PID 2>/dev/null
        exit 1
    fi
fi

# Activate virtual environment
source venv/Scripts/activate

# Install dependencies
if [ ! -f "requirements.txt" ]; then
    echo "Warning: requirements.txt not found, creating basic requirements..."
    cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==1.10.12
python-dotenv==1.0.0
EOF
fi

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install backend dependencies"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

# Start backend in background
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend server starting on http://localhost:8000 (PID: $BACKEND_PID)"

echo
echo "============================================"
echo "Writer Assistant Development Environment"
echo "============================================"
echo "Frontend: http://localhost:4200"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "============================================"
echo
echo "Logs are being written to frontend.log and backend.log"
echo "Press Ctrl+C to stop both servers"
echo

# Wait for user interrupt
wait
