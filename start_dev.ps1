# Flight Test System - Development Startup Script (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Flight Test System - Dev Environment  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "[INFO] No .env file found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

Write-Host "[1/3] Starting Backend (uvicorn)..." -ForegroundColor Green
$backendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru -WindowStyle Normal

Write-Host "[2/3] Starting Celery Worker..." -ForegroundColor Green
$celeryProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; celery -A app.celery_app worker -l info" -PassThru -WindowStyle Normal

Write-Host "[3/3] Starting Frontend (Vite)..." -ForegroundColor Green
$frontendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "All services started!" -ForegroundColor Cyan
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Kill processes
$backendProc | Stop-Process -Force -ErrorAction SilentlyContinue
$celeryProc | Stop-Process -Force -ErrorAction SilentlyContinue
$frontendProc | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "All services stopped." -ForegroundColor Red
