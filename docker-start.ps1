# Docker 一键启动脚本
# 用法: .\docker-start.ps1

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Flight Test System - Docker Deploy" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker not found!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    exit 1
}

# Check Docker Compose
$composeCmd = "docker compose"
try {
    docker compose version 2>&1 | Out-Null
} catch {
    try {
        docker-compose version 2>&1 | Out-Null
        $composeCmd = "docker-compose"
    } catch {
        Write-Host "[ERROR] Docker Compose not found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[1/3] Building images..." -ForegroundColor Yellow
Invoke-Expression "$composeCmd build"

Write-Host "[2/3] Starting services..." -ForegroundColor Yellow
Invoke-Expression "$composeCmd up -d"

Write-Host "[3/3] Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost" -ForegroundColor Yellow
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  MinIO:     http://localhost:9001" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Default: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "  Commands:" -ForegroundColor White
Write-Host "    View logs:  docker compose logs -f" -ForegroundColor Gray
Write-Host "    Stop:       docker compose down" -ForegroundColor Gray
Write-Host "    Restart:    docker compose restart" -ForegroundColor Gray
Write-Host "    Rebuild:    docker compose up -d --build" -ForegroundColor Gray
Write-Host ""
