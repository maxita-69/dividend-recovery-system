$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDir

Write-Host "============================================"
Write-Host "Dividend Recovery Trading System - STOP"
Write-Host "============================================"

# Ferma dai PID file
Get-ChildItem -Path ".pid_*" -ErrorAction SilentlyContinue | ForEach-Object {
    $pidVal = Get-Content $_.FullName
    Write-Host "Arresto $($_.Name) PID $pidVal..."
    taskkill /F /PID $pidVal | Out-Null
    Remove-Item $_.FullName -ErrorAction SilentlyContinue
}

# Fallback: libera le porte per PID specifico
Write-Host "Verifica porte residue..."
foreach ($port in @(8501, 8502, 4200)) {
    $conn = netstat -ano | Select-String ":$port" | Select-String "LISTENING"
    if ($conn) {
        $pidVal = ($conn -split '\s+')[-1]
        Write-Host "Porta $port occupata da PID $pidVal. Arresto..."
        taskkill /F /PID $pidVal | Out-Null
    }
}

Write-Host ""
Write-Host "Servizi arrestati."
Read-Host "Premi INVIO per chiudere..."
