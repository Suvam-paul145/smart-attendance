@echo off
echo Starting Smart Attendance Services...

:: Start Frontend (Next.js)
start "Frontend" cmd /k "cd frontend && npm run dev"

:: Start ML Service (FastAPI - Port 8001)
start "ML Service" cmd /k "cd server\ml-service && python -m uvicorn app.main:app --port 8001 --reload"

:: Start Backend API (FastAPI - Port 8000)
start "Backend API" cmd /k "cd server\backend-api && python -m uvicorn app.main:app --port 8000 --reload"

echo All services started in separate windows.
pause
