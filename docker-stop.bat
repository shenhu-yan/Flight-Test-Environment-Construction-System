@echo off
chcp 65001 >nul 2>&1
title Flight Test System - Stop

echo Stopping all services...
docker compose down 2>nul || docker-compose down
echo.
echo All services stopped.
pause
