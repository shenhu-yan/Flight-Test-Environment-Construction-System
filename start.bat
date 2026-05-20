@echo off
chcp 65001 >nul 2>&1
title Flight Test Environment - Starting...

echo Starting Flight Test Environment Construction System...
echo.

REM Start Backend
echo [1/3] Starting Backend Server...
start "Backend" powershell -NoExit -Command "cd '%~dp0backend'; if (Test-Path 'venv\Scripts\python.exe') { & 'venv\Scripts\python.exe' run.py } else { python run.py }"

REM Start Celery
echo [2/3] Starting Celery Worker...
start "Celery" powershell -NoExit -Command "cd '%~dp0backend'; if (Test-Path 'venv\Scripts\python.exe') { & 'venv\Scripts\python.exe' -m celery -A app.celery_app worker --loglevel=info } else { python -m celery -A app.celery_app worker --loglevel=info }"

REM Start Frontend
echo [3/3] Starting Frontend Server...
start "Frontend" powershell -NoExit -Command "cd '%~dp0frontend'; npm run dev"

echo.
echo All services started!
echo.
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo   Default: admin / admin123
echo.
pause
