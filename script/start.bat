@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0.."
echo ============================================
echo Dividend Recovery Trading System - START
echo ============================================

:: 1. Virtual environment
if not exist venv (
    echo [1/4] Creazione virtual environment...
    python -m venv venv
    echo         Installazione dipendenze Python puo richiedere tempo...
    venv\Scripts\pip.exe install -r requirements.txt -q
) else (
    echo [1/4] Virtual environment OK
)

:: 2. Libera porte
echo [2/4] Verifica porte...
for %%p in (8501 8502 4200) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p" ^| findstr "LISTENING"') do (
        echo         Porta %%p occupata, PID %%a. Libero...
        taskkill /F /PID %%a >nul 2>&1
    )
)
ping -n 2 127.0.0.1 >nul

:: 3. Avvio servizi
echo [3/4] Avvio servizi...
echo         Streamlit Dashboard -^> http://localhost:8501
powershell -Command "Start-Process -FilePath 'venv\Scripts\streamlit.exe' -ArgumentList 'run','app/Home.py','--server.port','8501','--browser.gatherUsageStats','false' -WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id | Out-File .pid_streamlit1"
ping -n 4 127.0.0.1 >nul

echo         Dividend Calendar   -^> http://localhost:8502
powershell -Command "Start-Process -FilePath 'venv\Scripts\streamlit.exe' -ArgumentList 'run','dashboard/app.py','--server.port','8502','--browser.gatherUsageStats','false' -WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id | Out-File .pid_streamlit2"
ping -n 4 127.0.0.1 >nul

echo         Angular Frontend    -^> http://localhost:4200
start "Angular" /min cmd /c "cd frontend && npm run start"
echo         Attesa compilazione Angular...

:: Polling per Angular (max 40s)
for /l %%i in (1,1,40) do (
    netstat -ano | findstr ":4200" | findstr "LISTENING" >nul
    if not errorlevel 1 goto :angular_ok
    ping -n 2 127.0.0.1 >nul
)
echo         ATTENZIONE: Angular non risponde entro 40s
goto :verify

:angular_ok

:: 4. Verifica
:verify
echo [4/4] Verifica avvio...
set OK=1
for %%p in (8501 8502 4200) do (
    netstat -ano | findstr ":%%p" | findstr "LISTENING" >nul
    if errorlevel 1 (
        echo         Porta %%p -^> NON ATTIVA
        set OK=0
    ) else (
        echo         Porta %%p -^> OK
    )
)

echo.
if !OK! == 1 (
    echo ============================================
    echo TUTTI I SERVIZI ATTIVI
    echo - http://localhost:8501  Dashboard
    echo - http://localhost:8502  Calendar
    echo - http://localhost:4200  Angular
    echo ============================================
) else (
    echo ATTENZIONE: alcuni servizi non sono attivi.
    echo Controlla i log: streamlit1.log, streamlit2.log, angular.log
)

echo.
echo Per arrestare: script\stop.bat
pause
