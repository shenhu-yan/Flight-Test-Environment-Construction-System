@echo off
chcp 65001 >nul 2>&1
title Flight Test Environment - Setup

echo ============================================
echo   Flight Test Environment - Quick Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Creating backend virtual environment...
cd /d "%~dp0backend"
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo [2/4] Installing Python dependencies (may take a few minutes)...
pip install -r requirements.txt -q

echo [3/4] Installing frontend npm dependencies...
cd /d "%~dp0frontend"
call npm install --silent

echo [4/4] Creating database...
psql -U postgres -c "CREATE DATABASE fltect;" 2>nul

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo   Run: start_dev.ps1
echo   Or double-click start.bat
echo.
echo   Default: admin / admin123
echo   URL: http://localhost:5173
echo.
pause
