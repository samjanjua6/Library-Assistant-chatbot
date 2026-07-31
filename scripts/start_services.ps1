Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Starting Zylo Library Services            " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$projectDir = $PSScriptRoot | Split-Path -Parent
Set-Location $projectDir

# 1. Start Redis
Write-Host "Starting Redis..." -ForegroundColor Yellow
$redisPath = "$env:USERPROFILE\Downloads\ZyloSetup\Redis\redis-server.exe"
if (Test-Path $redisPath) {
    Start-Process -FilePath $redisPath -WindowStyle Minimized
} else {
    Write-Host "WARNING: Redis server not found at $redisPath" -ForegroundColor Red
}

# 2. Check Virtual Environment
if (-Not (Test-Path "$projectDir\.venv")) {
    Write-Host "Virtual environment not found! Creating and installing dependencies..." -ForegroundColor Yellow
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

# 3. Start Backend (Uvicorn)
Write-Host "Starting FastAPI Backend..." -ForegroundColor Yellow
Start-Process -FilePath "$projectDir\.venv\Scripts\uvicorn.exe" -ArgumentList "app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Minimized

# 4. Start Worker (ARQ)
Write-Host "Starting ARQ Background Worker..." -ForegroundColor Yellow
$env:PYTHONPATH = $projectDir
Start-Process -FilePath "$projectDir\.venv\Scripts\arq.exe" -ArgumentList "app.worker.worker.WorkerSettings" -WindowStyle Minimized

# 5. Start Caddy
Write-Host "Starting Caddy (Web Server)..." -ForegroundColor Yellow
$caddyPath = "$projectDir\caddy.exe"
if (Test-Path $caddyPath) {
    Start-Process -FilePath $caddyPath -ArgumentList "run" -WindowStyle Minimized
} else {
    Write-Host "WARNING: caddy.exe not found in $projectDir" -ForegroundColor Red
}

Write-Host "All services have been launched in background windows!" -ForegroundColor Green
Write-Host "Close those windows when you want to stop the server." -ForegroundColor White
