Write-Host "Starting Flight Test Environment Construction System..." -ForegroundColor Green

# 检测虚拟环境
$backendCmd = "python"
if (Test-Path "$PSScriptRoot\backend\venv\Scripts\python.exe") {
    $backendCmd = "$PSScriptRoot\backend\venv\Scripts\python.exe"
    Write-Host "`n  Using virtual environment" -ForegroundColor DarkGray
}

Write-Host "`n[1/3] Starting Backend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; & '$backendCmd' run.py"

Write-Host "[2/3] Starting Celery Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; & '$backendCmd' -m celery -A app.celery_app worker --loglevel=info"

Write-Host "[3/3] Starting Frontend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "Celery Worker: Running in background" -ForegroundColor Yellow
