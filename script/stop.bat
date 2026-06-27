@echo off
setlocal

cd /d "%~dp0.."
echo ============================================
echo Dividend Recovery Trading System - STOP
echo ============================================

:: Ferma dai PID file
if exist .pid_* (
    for %%f in (.pid_*) do (
        if exist %%f (
            for /f %%i in (%%f) do (
                echo Arresto %%f PID %%i...
                taskkill /F /PID %%i >nul 2>&1
            )
            del %%f 2>nul
        )
    )
)

:: Fallback: libera le porte per PID specifico
echo Verifica porte residue...
for %%p in (8501 4200) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p" ^| findstr "LISTENING"') do (
        echo Porta %%p occupata da PID %%a. Arresto...
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo.
echo Servizi arrestati.
pause
