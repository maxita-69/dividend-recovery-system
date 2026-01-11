@echo off
REM Dividend Recovery System - Update Calendario Dividendi
REM Doppio click per aggiornare dati e calendario

echo ========================================
echo  Dividend Recovery System
echo  Update Calendario Dividendi
echo ========================================
echo.

REM Naviga alla directory del progetto
cd /d "%~dp0"

REM Attiva virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [1/3] Attivazione virtual environment...
    call venv\Scripts\activate.bat
    echo      OK
    echo.
) else (
    echo ERROR: Virtual environment non trovato!
    echo Esegui prima: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Aggiorna dati storici (incrementale)
echo [2/3] Aggiornamento dati storici...
echo      (Questo puo richiedere alcuni minuti)
echo.
python download_stock_data_v2.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Errore durante download dati
    pause
    exit /b 1
)
echo      OK
echo.

REM Aggiorna calendario dividendi
echo [3/3] Aggiornamento calendario dividendi...
echo.
python dividend_calendar.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Errore durante aggiornamento calendario
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Update completato con successo!
echo ========================================
echo.
echo Puoi ora:
echo  - Visualizzare il calendario: python dividend_calendar.py
echo  - Avviare la dashboard: start_dashboard.bat
echo.

pause
