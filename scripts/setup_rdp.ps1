Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Zylo Library Assistant - RDP Native Setup " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$downloadDir = "$env:USERPROFILE\Downloads\ZyloSetup"
if (-Not (Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir | Out-Null
}

Write-Host "`n[1/5] Downloading Python 3.11..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$downloadDir\python-installer.exe"

Write-Host "[2/5] Downloading Node.js (v20 LTS)..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.15.1/node-v20.15.1-x64.msi" -OutFile "$downloadDir\node-installer.msi"

Write-Host "[3/5] Downloading PostgreSQL 16..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://get.enterprisedb.com/postgresql/postgresql-16.3-1-windows-x64.exe" -OutFile "$downloadDir\postgres-installer.exe"

Write-Host "[4/5] Downloading Redis (Windows Native Port)..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip" -OutFile "$downloadDir\redis.zip"
Expand-Archive -Path "$downloadDir\redis.zip" -DestinationPath "$downloadDir\Redis" -Force

Write-Host "[5/5] Downloading Caddy (Web Server & SSL)..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://caddyserver.com/api/download?os=windows&arch=amd64" -OutFile "$downloadDir\caddy.exe"

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "   DOWNLOADS COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "All files are saved in: $downloadDir" -ForegroundColor White
Write-Host "`nPlease run the installers manually in this order:"
Write-Host "1. python-installer.exe (IMPORTANT: Check the box 'Add Python.exe to PATH' at the bottom!)"
Write-Host "2. node-installer.msi (Just click Next all the way through)"
Write-Host "3. postgres-installer.exe (Remember the password you set for the 'postgres' user!)"
Write-Host "`nFor Redis and Caddy:"
Write-Host "- Redis is in the 'Redis' folder. You just run redis-server.exe to start it."
Write-Host "- Move caddy.exe to your main project folder."
