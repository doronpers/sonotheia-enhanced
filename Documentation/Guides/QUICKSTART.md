# 🚀 Sonotheia Enhanced - Quick Start Guide

Get the test environment and dashboard running in seconds!

## 🎯 Fastest Way to Start

### Option 1: One-Command Setup (Recommended)

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

The script automatically:
- ✓ Detects if Docker is available
- ✓ Installs all dependencies  
- ✓ Starts backend API (port 8000)
- ✓ Starts frontend dashboard (port 3000)

### Option 2: Docker Compose

If you have Docker installed:

```bash
docker compose up --build
# OR (for Docker Compose v1)
docker-compose up --build
```

## 🌐 Access the Application

Once started, open your browser:

- **Dashboard:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **Backend API:** http://localhost:8000

## 🛑 Stopping Services

**Using scripts:**
```bash
./stop.sh      # Linux/Mac
stop.bat       # Windows
```

**Using Docker:**
```bash
docker compose down
# OR (for Docker Compose v1)
docker-compose down
```

**Or simply:** Press `Ctrl+C` in the terminal

## 📋 Prerequisites

### For Docker Setup (Recommended)
- Docker Desktop or Docker Engine
- Docker Compose

### For Local Setup (Fallback)
- Python 3.11+ (Note: Python 3.12+ not supported due to dependencies)
- Node.js 18+ and npm
- Git

## 🔧 Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` if needed (optional for demo mode)

## 📖 What's Included

### Backend (FastAPI)
- Multi-factor authentication API
- Voice deepfake detection
- SAR (Suspicious Activity Report) generation
- Transaction risk assessment
- Interactive API documentation

### Frontend (React)
- Interactive waveform dashboard
- Real-time authentication visualization
- Factor-level explainability cards
- Evidence detail views

## 🐛 Common Issues

### "Port already in use"
```bash
# Kill process on port 8000 or 3000
lsof -ti:8000 | xargs kill -9    # Linux/Mac
# Or use the stop script
./stop.sh
```

### "Docker build failed"
```bash
# Clear Docker cache
docker system prune -a
docker compose up --build
```

### "Module not found" (Python)
```bash
cd backend
pip install -r requirements.txt
```

### "npm install failed"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

## 📚 Next Steps

1. ✅ Start the services (see above)
2. 📖 Read the [README.md](../../README.md) for detailed documentation
3. 🧪 Try the demo endpoints at http://localhost:8000/docs
4. 🎨 Explore the dashboard at http://localhost:3000
5. 📊 Review [API.md](../API.md) for API reference

## 💡 Tips

- **Demo Mode:** Enabled by default, safe for testing
- **Hot Reload:** Backend and frontend auto-reload on code changes
- **Logs:** 
  - Docker: `docker compose logs -f`
  - Local: Check `backend.log` and `frontend.log`
- **Health Check:** Visit http://localhost:8000/ to verify backend

## 🆘 Need Help?

- Check troubleshooting section in [README.md](../../README.md)
- Review logs for error messages
- Ensure all ports (3000, 8000) are available
- Verify Docker is running (if using Docker)

---

**Ready in seconds. Test immediately. Deploy confidently.**
