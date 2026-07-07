# Start Meet Greek Singles locally (MariaDB + PHP built-in server).
# Usage:  powershell -ExecutionPolicy Bypass -File _local_run\start-local.ps1

$ErrorActionPreference = 'Stop'
$mariadbd = "C:\Program Files\MariaDB 12.3\bin\mariadbd.exe"
$runDir   = $PSScriptRoot
$webroot  = Join-Path $runDir 'webroot'
$router   = Join-Path $runDir 'router.php'
$phpPort  = 8080

# 1. Start MariaDB if it isn't already listening on 3306.
$dbUp = Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue
if (-not $dbUp) {
    Write-Host "Starting MariaDB..." -ForegroundColor Cyan
    Start-Process -FilePath $mariadbd -ArgumentList '--console' -WindowStyle Hidden
    Start-Sleep -Seconds 4
} else {
    Write-Host "MariaDB already running on 3306." -ForegroundColor Green
}

# 2. Free port 8080 if something is on it.
$old = (Get-NetTCPConnection -LocalPort $phpPort -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($old) { Stop-Process -Id $old -Force -ErrorAction SilentlyContinue }

# 3. Start the PHP built-in server (foreground).
Write-Host "Serving http://127.0.0.1:$phpPort  (Ctrl+C to stop)" -ForegroundColor Cyan
& php -S "127.0.0.1:$phpPort" -t $webroot $router
