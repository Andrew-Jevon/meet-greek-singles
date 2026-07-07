# Start BOTH local instances of Meet Greek Singles.
#   :8080  git-copy webroot  (system MariaDB on 3306)
#   :8081  origin webroot     (portable MariaDB on 3307)
# Usage:  powershell -ExecutionPolicy Bypass -File _local_run\start-both.ps1

$ErrorActionPreference = 'SilentlyContinue'

$sysMariadbd  = "C:\Program Files\MariaDB 12.3\bin\mariadbd.exe"
$portMariadbd = "D:\MyProjects\Irene\_local\mariadb\mariadb-10.11.10-winx64\bin\mariadbd.exe"
$portData     = "D:\MyProjects\Irene\_local\mariadb_data"

$gitRun   = "C:\Users\com\Desktop\meet-greek-singles\_local_run"   # has webroot\ + router.php
$originRun = "D:\MyProjects\Irene\_local"                          # has webroot\ + router.php

function Test-Port($p) { [bool](Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue) }

# --- databases ---
if (-not (Test-Port 3306)) {
    Write-Host "Starting system MariaDB (3306)..." -ForegroundColor Cyan
    Start-Process -FilePath $sysMariadbd -ArgumentList '--console' -WindowStyle Hidden
} else { Write-Host "MariaDB 3306 already up." -ForegroundColor Green }

if (-not (Test-Port 3307)) {
    Write-Host "Starting portable MariaDB (3307)..." -ForegroundColor Cyan
    Start-Process -FilePath $portMariadbd -ArgumentList "--datadir=$portData","--port=3307","--console" -WindowStyle Hidden
} else { Write-Host "MariaDB 3307 already up." -ForegroundColor Green }

Start-Sleep -Seconds 5

# --- web servers ---
foreach ($i in @(@{port=8080; dir=$gitRun; name='git-copy'}, @{port=8081; dir=$originRun; name='origin'})) {
    $old = (Get-NetTCPConnection -LocalPort $i.port -State Listen -ErrorAction SilentlyContinue).OwningProcess
    if ($old) { Stop-Process -Id $old -Force -ErrorAction SilentlyContinue }
    Write-Host ("Starting {0} on http://127.0.0.1:{1}" -f $i.name, $i.port) -ForegroundColor Cyan
    Start-Process -FilePath 'php' -ArgumentList "-S","127.0.0.1:$($i.port)","-t","webroot","router.php" -WorkingDirectory $i.dir -WindowStyle Hidden
}

Start-Sleep -Seconds 2
Write-Host ""
Write-Host "Both instances launched:" -ForegroundColor Green
Write-Host "  git-copy -> http://127.0.0.1:8080"
Write-Host "  origin   -> http://127.0.0.1:8081"
