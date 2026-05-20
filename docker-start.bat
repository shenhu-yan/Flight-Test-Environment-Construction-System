@echo off
chcp 65001 >nul 2>&1
title Flight Test System - Docker Deploy

echo ============================================
echo   Flight Test System - Docker Deploy
echo ============================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found!
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [1/3] Building images...
docker compose build
if errorlevel 1 (
    docker-compose build
)

echo [2/3] Starting services...
docker compose up -d
if errorlevel 1 (
    docker-compose up -d
)

echo [3/3] Waiting for services...
timeout /t 10 /nobreak >nul

echo.
echo ============================================
echo   All services started!
echo ============================================
echo.
echo   Frontend:  http://localhost
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   MinIO:     http://localhost:9001
echo.
echo   Default: admin / admin123
echo.
echo   Commands:
echo     View logs:  docker compose logs -f
echo     Stop:       docker compose down
echo     Restart:    docker compose restart
echo     Rebuild:    docker compose up -d --build
echo.
pause
