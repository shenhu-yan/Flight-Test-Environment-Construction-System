#!/usr/bin/env bash
# Flight Test System - Development Startup Script

set -e

echo "========================================"
echo "  Flight Test System - Dev Environment  "
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "[INFO] No .env file found. Copying from .env.example..."
    cp .env.example .env
fi

# Cleanup on exit
cleanup() {
    echo ""
    echo "[INFO] Stopping all services..."
    kill $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null || true
    echo "[OK] All services stopped."
}
trap cleanup EXIT INT TERM

echo "[1/3] Starting Backend (uvicorn)..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo "[2/3] Starting Celery Worker..."
cd backend
celery -A app.celery_app worker -l info &
CELERY_PID=$!
cd ..

echo "[3/3] Starting Frontend (Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "All services started!"
echo "  Backend  : http://localhost:8000"
echo "  Frontend : http://localhost:3000"
echo "  API Docs : http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

wait
