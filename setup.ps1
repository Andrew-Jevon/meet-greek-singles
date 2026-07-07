# Meet Greek Singles - one-shot local setup (clone-and-run).
# Assembles the runnable webroot, writes local db.php, and imports the database.
#
#   powershell -ExecutionPolicy Bypass -File setup.ps1
#
# Prerequisites:
#   - PHP 8.2+ on PATH with the mysqli extension enabled
#   - MariaDB/MySQL running locally (root reachable) - client mariadb/mysql on PATH
#
# After setup, start the site with:  _local_run\start-local.ps1

param(
    [string]$DbHost = 'localhost',
    [string]$DbName = 'chamo',
    [string]$DbUser = 'chamo_user',
    [string]$DbPass = 'AdminR@123#',
    [string]$MysqlBin = ''
)
$ErrorActionPreference = 'Stop'
$root     = $PSScriptRoot
$core     = Join-Path $root '_core_extract\chameleon_social_software_5.7'
$upstream = Join-Path $root 'upstream'
$webroot  = Join-Path $root '_local_run\webroot'
$dump     = Join-Path $root 'db\meetgreeksingles.sql'

Write-Host '== 1/4  Assembling webroot (core + upstream overlay) ==' -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $webroot | Out-Null
robocopy $core     $webroot /E /NFL /NDL /NJH /NJS /NP | Out-Null
robocopy $upstream $webroot /E /NFL /NDL /NJH /NJS /NP | Out-Null
Write-Host "   webroot ready: $webroot" -ForegroundColor Green

Write-Host '== 2/4  Writing local db.php ==' -ForegroundColor Cyan
$cfgDir = Join-Path $webroot '_include\config'
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$q = [char]34   # double-quote
$lines = @(
    '<?php',
    ('$g[' + $q + 'db' + $q + '][' + $q + 'host' + $q + "] = htmlspecialchars_decode('$DbHost');"),
    ('$g[' + $q + 'db' + $q + '][' + $q + 'db' + $q + "] = htmlspecialchars_decode('$DbName');"),
    ('$g[' + $q + 'db' + $q + '][' + $q + 'user' + $q + "] = htmlspecialchars_decode('$DbUser');"),
    ('$g[' + $q + 'db' + $q + '][' + $q + 'password' + $q + "] = htmlspecialchars_decode('$DbPass');"),
    '?>'
)
Set-Content -Path (Join-Path $cfgDir 'db.php') -Value $lines -Encoding utf8
Write-Host "   wrote $cfgDir\db.php" -ForegroundColor Green

Write-Host '== 3/4  Locating MySQL/MariaDB client ==' -ForegroundColor Cyan
if (-not $MysqlBin) {
    $cand = @(
        (Get-Command mariadb -ErrorAction SilentlyContinue).Source,
        (Get-Command mysql   -ErrorAction SilentlyContinue).Source,
        'C:\Program Files\MariaDB 12.3\bin\mariadb.exe'
    ) | Where-Object { $_ -and (Test-Path $_) }
    $MysqlBin = $cand | Select-Object -First 1
}
if (-not $MysqlBin) {
    Write-Host '   No MySQL client found. Create the DB and import db\meetgreeksingles.sql manually.' -ForegroundColor Yellow
    exit 0
}

Write-Host '== 4/4  Creating database + user and importing dump ==' -ForegroundColor Cyan
$sql = "CREATE DATABASE IF NOT EXISTS $DbName CHARACTER SET utf8mb4;"
$sql += " CREATE USER IF NOT EXISTS '$DbUser'@'$DbHost' IDENTIFIED BY '$DbPass';"
$sql += " GRANT ALL PRIVILEGES ON $DbName.* TO '$DbUser'@'$DbHost'; FLUSH PRIVILEGES;"
& $MysqlBin -u root -e $sql
Get-Content $dump -Raw | & $MysqlBin -u root $DbName
$tables = (& $MysqlBin -u root $DbName -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DbName';")
Write-Host "   imported - $tables tables in '$DbName'" -ForegroundColor Green

Write-Host ''
Write-Host 'Setup complete. Start the site with:' -ForegroundColor Green
Write-Host '   powershell -ExecutionPolicy Bypass -File _local_run\start-local.ps1'
Write-Host '   then open http://127.0.0.1:8080'
