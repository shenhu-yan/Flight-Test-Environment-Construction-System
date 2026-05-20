# Flight Test Environment Construction System - 一键安装脚本
# 用法: 右键 -> 使用 PowerShell 运行

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  飞行试验环境构建系统 - 一键安装" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ========== 工具函数 ==========
function Test-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Write-Step($step, $msg) {
    Write-Host "`n[$step] $msg" -ForegroundColor Yellow
}

function Write-OK($msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}

function Write-Skip($msg) {
    Write-Host "  [SKIP] $msg" -ForegroundColor DarkGray
}

function Write-Fail($msg) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
}

# ========== 1. 检查 Python ==========
Write-Step "1/7" "检查 Python..."

$pythonOk = $false
if (Test-Command "python") {
    $pyVer = python --version 2>&1
    if ($pyVer -match "Python 3\.(\d+)") {
        $minor = [int]$Matches[1]
        if ($minor -ge 10) {
            Write-OK "已安装 $pyVer"
            $pythonOk = $true
        } else {
            Write-Fail "版本过低 ($pyVer)，需要 Python 3.10+"
        }
    }
} else {
    Write-Fail "未检测到 Python"
}

if (-not $pythonOk) {
    Write-Host ""
    Write-Host "  请安装 Python 3.10+: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  安装时勾选 'Add Python to PATH'" -ForegroundColor White
    $ans = Read-Host "`n  安装完成后按回车继续，或输入 q 退出"
    if ($ans -eq "q") { exit 1 }
    # 重新检测
    if (Test-Command "python") {
        $pythonOk = $true
        Write-OK "Python 已就绪"
    } else {
        Write-Fail "仍然无法检测到 Python，退出"
        exit 1
    }
}

# ========== 2. 检查 Node.js ==========
Write-Step "2/7" "检查 Node.js..."

$nodeOk = $false
if (Test-Command "node") {
    $nodeVer = node --version 2>&1
    Write-OK "已安装 $nodeVer"
    $nodeOk = $true
} else {
    Write-Fail "未检测到 Node.js"
}

if (-not $nodeOk) {
    Write-Host ""
    Write-Host "  请安装 Node.js 18+: https://nodejs.org/" -ForegroundColor White
    $ans = Read-Host "`n  安装完成后按回车继续，或输入 q 退出"
    if ($ans -eq "q") { exit 1 }
    if (Test-Command "node") {
        $nodeOk = $true
        Write-OK "Node.js 已就绪"
    } else {
        Write-Fail "仍然无法检测到 Node.js，退出"
        exit 1
    }
}

# ========== 3. 检查/启动 PostgreSQL ==========
Write-Step "3/7" "检查 PostgreSQL..."

$pgOk = $false
if (Test-Command "psql") {
    $pgOk = $true
    Write-OK "psql 已在 PATH 中"
} else {
    # 常见安装路径
    $pgPaths = @(
        "C:\Program Files\PostgreSQL\17\bin\psql.exe",
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe",
        "C:\Program Files\PostgreSQL\14\bin\psql.exe"
    )
    foreach ($p in $pgPaths) {
        if (Test-Path $p) {
            $env:PATH += ";$(Split-Path $p)"
            $pgOk = $true
            Write-OK "找到 PostgreSQL: $p"
            break
        }
    }
}

if (-not $pgOk) {
    Write-Fail "未检测到 PostgreSQL"
    Write-Host "  请安装 PostgreSQL 14+: https://www.postgresql.org/download/windows/" -ForegroundColor White
    $ans = Read-Host "`n  安装完成后按回车继续，或输入 q 退出"
    if ($ans -eq "q") { exit 1 }
    exit 1
}

# 检查 PostgreSQL 服务是否运行
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pgService) {
    if ($pgService.Status -ne "Running") {
        Write-Host "  启动 PostgreSQL 服务..." -ForegroundColor White
        Start-Service $pgService.Name -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    Write-OK "PostgreSQL 服务运行中"
} else {
    Write-Skip "未找到 PostgreSQL 服务，请确保已启动"
}

# ========== 4. 检查/启动 Redis ==========
Write-Step "4/7" "检查 Redis..."

$redisOk = $false
if (Test-Command "redis-cli") {
    $redisOk = $true
    Write-OK "redis-cli 已在 PATH 中"
} else {
    $redisPaths = @(
        "C:\Program Files\Redis\redis-cli.exe",
        "C:\Redis\redis-cli.exe"
    )
    foreach ($p in $redisPaths) {
        if (Test-Path $p) {
            $env:PATH += ";$(Split-Path $p)"
            $redisOk = $true
            Write-OK "找到 Redis: $p"
            break
        }
    }
}

if (-not $redisOk) {
    Write-Fail "未检测到 Redis"
    Write-Host "  请安装 Redis: https://github.com/tporadowski/redis/releases" -ForegroundColor White
    $ans = Read-Host "`n  安装完成后按回车继续，或输入 q 退出"
    if ($ans -eq "q") { exit 1 }
    exit 1
}

# 检查 Redis 服务
$redisService = Get-Service -Name "Redis*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($redisService) {
    if ($redisService.Status -ne "Running") {
        Write-Host "  启动 Redis 服务..." -ForegroundColor White
        Start-Service $redisService.Name -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    Write-OK "Redis 服务运行中"
} else {
    Write-Skip "未找到 Redis 服务，请确保已启动"
}

# ========== 5. 创建数据库 ==========
Write-Step "5/7" "初始化数据库..."

$dbExists = $false
try {
    $result = psql -U postgres -t -c "SELECT 1 FROM pg_database WHERE datname='fltect'" 2>&1
    if ($result -match "1") {
        $dbExists = $true
    }
} catch {}

if (-not $dbExists) {
    Write-Host "  创建数据库 fltect..." -ForegroundColor White
    try {
        psql -U postgres -c "CREATE DATABASE fltect;" 2>&1 | Out-Null
        Write-OK "数据库创建成功"
    } catch {
        Write-Fail "创建数据库失败，请手动执行: psql -U postgres -c ""CREATE DATABASE fltect;"""
    }
} else {
    Write-OK "数据库 fltect 已存在"
}

# ========== 6. 安装后端依赖 ==========
Write-Step "6/7" "安装后端 Python 依赖..."

Push-Location "$ProjectRoot\backend"
if (-not (Test-Path "venv")) {
    Write-Host "  创建虚拟环境..." -ForegroundColor White
    python -m venv venv
}

# 激活虚拟环境
& "$ProjectRoot\backend\venv\Scripts\Activate.ps1"

Write-Host "  安装依赖 (可能需要几分钟)..." -ForegroundColor White
pip install -r requirements.txt -q
Write-OK "后端依赖安装完成"
Pop-Location

# ========== 7. 安装前端依赖 ==========
Write-Step "7/7" "安装前端 npm 依赖..."

Push-Location "$ProjectRoot\frontend"
npm install --silent
Write-OK "前端依赖安装完成"
Pop-Location

# ========== 完成 ==========
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  安装完成!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  启动方式:" -ForegroundColor White
Write-Host "    .\start_dev.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  或手动启动:" -ForegroundColor White
Write-Host "    后端: cd backend && .\venv\Scripts\python run.py" -ForegroundColor Gray
Write-Host "    前端: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  访问地址: http://localhost:5173" -ForegroundColor Yellow
Write-Host "  默认账号: admin / admin123" -ForegroundColor Yellow
Write-Host ""
