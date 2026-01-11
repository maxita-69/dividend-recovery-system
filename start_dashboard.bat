@echo off
REM Dividend Recovery System - Avvia Dashboard
REM Doppio click per avviare il sito Streamlit

echo ========================================
echo  Dividend Recovery System
echo  Avvio Dashboard Web...
echo ========================================
echo.

REM Naviga alla directory del progetto
cd /d "%~dp0"

REM Attiva virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [1/2] Attivazione virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment non trovato!
    echo Assicurati di aver eseguito: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Avvia Streamlit
echo [2/2] Avvio dashboard...
echo.
echo Dashboard disponibile su: http://localhost:8501
echo Premi CTRL+C per fermare il server
echo.

streamlit run dashboard\app.py

pause
