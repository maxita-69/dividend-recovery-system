$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDir

Write-Host "============================================"
Write-Host "Dividend Recovery Trading System - START"
Write-Host "============================================"

# 1. Virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "[1/4] Creazione virtual environment..."
    python -m venv venv
    Write-Host "        Installazione dipendenze Python..."
    & "venv\Scripts\pip.exe" install -r requirements.txt -q
} else {
    Write-Host "[1/4] Virtual environment OK"
}

# 2. Libera porte
Write-Host "[2/4] Verifica porte..."
foreach ($port in @(8501, 8502, 4200)) {
    $conn = netstat -ano | Select-String ":$port" | Select-String "LISTENING"
    if ($conn) {
        $pid = ($conn -split '\s+')[-1]
        Write-Host "        Porta $port occupata (PID $pid). Libero..."
        taskkill /F /PID $pid | Out-Null
    }
}
Start-Sleep -Seconds 2

# 3. Avvio servizi
Write-Host "[3/4] Avvio servizi..."

Write-Host "        Streamlit Dashboard -> http://localhost:8501"
$st1 = Start-Process -FilePath "venv\Scripts\streamlit.exe" -ArgumentList "run","app/Home.py","--server.port","8501","--browser.gatherUsageStats","false" -WindowStyle Hidden -PassThru
$st1.Id | Out-File .pid_streamlit1
Start-Sleep -Seconds 3

Write-Host "        Dividend Calendar   -> http://localhost:8502"
$st2 = Start-Process -FilePath "venv\Scripts\streamlit.exe" -ArgumentList "run","dashboard/app.py","--server.port","8502","--browser.gatherUsageStats","false" -WindowStyle Hidden -PassThru
$st2.Id | Out-File .pid_streamlit2
Start-Sleep -Seconds 3

Write-Host "        Angular Frontend    -> http://localhost:4200"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c","cd frontend && npm run start" -WindowStyle Normal
Write-Host "        Attesa compilazione Angular..."

# Polling per Angular (max 40s)
$angularReady = $false
for ($i = 0; $i -lt 40; $i++) {
    $conn = netstat -ano | Select-String ":4200" | Select-String "LISTENING"
    if ($conn) {
        $angularReady = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $angularReady) {
    Write-Host "        ATTENZIONE: Angular non risponde entro 40s"
}

# 4. Verifica
Write-Host "[4/4] Verifica avvio..."
$allOk = $true
foreach ($port in @(8501, 8502, 4200)) {
    $conn = netstat -ano | Select-String ":$port" | Select-String "LISTENING"
    if ($conn) {
        Write-Host "        Porta $port -> OK"
    } else {
        Write-Host "        Porta $port -> NON ATTIVA"
        $allOk = $false
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "============================================"
    Write-Host "TUTTI I SERVIZI ATTIVI"
    Write-Host "- http://localhost:8501  Dashboard"
    Write-Host "- http://localhost:8502  Calendar"
    Write-Host "- http://localhost:4200  Angular"
    Write-Host "============================================"
} else {
    Write-Host "ATTENZIONE: alcuni servizi non sono attivi."
    Write-Host "Controlla i log: streamlit1.log, streamlit2.log, angular.log"
}

Write-Host ""
Write-Host "Per arrestare: .\script\stop.ps1"
Read-Host "Premi INVIO per chiudere..."
