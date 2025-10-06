#!/bin/bash

echo "Stopping Writer Assistant Development Servers..."
echo

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service=$2
    echo "Stopping $service on port $port..."

    # Find and kill processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "Found processes: $pids"
        kill -9 $pids 2>/dev/null
        echo "$service stopped"
    else
        echo "No $service process found on port $port"
    fi
}

# Kill Angular development server (port 4200)
kill_port 4200 "Angular development server"

# Kill Python backend server (port 8000)
kill_port 8000 "Python backend server"

# Additional cleanup for any remaining processes
echo "Cleaning up any remaining processes..."

# Kill any ng serve processes
pkill -f "ng serve" 2>/dev/null

# Kill any uvicorn processes
pkill -f "uvicorn" 2>/dev/null

# Kill any node processes running on port 4200
pkill -f "node.*4200" 2>/dev/null

# Kill any python processes running on port 8000
pkill -f "python.*8000" 2>/dev/null

echo
echo "Writer Assistant development servers have been stopped."
echo

# Clean up log files if they exist
if [ -f "frontend/frontend.log" ]; then
    rm frontend/frontend.log
    echo "Frontend log file cleaned up"
fi

if [ -f "backend/backend.log" ]; then
    rm backend/backend.log
    echo "Backend log file cleaned up"
fi

echo "Cleanup complete."