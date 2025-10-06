# Writer Assistant - Helper Scripts

Simple helper scripts to start and stop the Writer Assistant development environment.

## Development Environment

### Starting Development Servers

**Windows:**
```bash
start-dev.bat
```

**Linux/macOS:**
```bash
./start-dev.sh
```

This will:
- Check for Node.js and Python installation
- Install frontend dependencies (if needed)
- Create Python virtual environment (if needed)
- Install backend dependencies (if needed)
- Start Angular development server on http://localhost:4200
- Start Python FastAPI server on http://localhost:8000

### Stopping Development Servers

**Windows:**
```bash
stop-dev.bat
```

**Linux/macOS:**
```bash
./stop-dev.sh
```

This will:
- Stop Angular development server (port 4200)
- Stop Python backend server (port 8000)
- Clean up any remaining processes
- Remove log files

## Production Environment

For production deployment, use Docker Compose directly:

```bash
# Start production environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop production environment
docker-compose down
```

## Script Features

### Development Scripts (`start-dev.*`, `stop-dev.*`)
- ✅ Automatic dependency checking
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Concurrent server startup
- ✅ Cross-platform support (Windows/Linux/macOS)
- ✅ Error handling and validation
- ✅ Log file generation
- ✅ Clean shutdown and process cleanup

## System Requirements

### Development Environment
- **Node.js** (v16 or higher)
- **npm** (comes with Node.js)
- **Python** (v3.8 or higher)
- **pip** (comes with Python)

### Production Environment
- **Docker** and **Docker Compose** (use standard docker-compose commands)

## Usage Examples

### Daily Development Workflow
```bash
# Start working
./start-dev.sh

# When done for the day
./stop-dev.sh
```

### Production Deployment
```bash
# Deploy
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop when needed
docker-compose down
```

## Log Files

Development logs are automatically created:
- `frontend/frontend.log` - Angular development server logs
- `backend/backend.log` - Python FastAPI server logs

View logs using:
- `tail -f frontend/frontend.log`
- `tail -f backend/backend.log`

## Troubleshooting

### Port Already in Use
If you get port conflicts:
```bash
# Stop all development servers
./stop-dev.sh

# Or manually kill processes
# Windows
netstat -ano | findstr :4200
netstat -ano | findstr :8000
taskkill /f /pid <PID>

# Linux/macOS
lsof -ti:4200 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Permission Issues (Linux/macOS)
```bash
# Make scripts executable
chmod +x *.sh
```

### Environment Cleanup
```bash
# Clean development environment manually
rm -rf frontend/node_modules
rm -rf backend/venv
rm -f frontend/frontend.log
rm -f backend/backend.log
```