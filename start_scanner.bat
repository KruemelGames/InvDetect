@echo off
:: InvDetect – Star Citizen Universal Inventory Scanner
title InvDetect - Star Citizen Scanner vFinal
cd /d "%~dp0"

:: Prüfen, ob schon als Admin
net session >nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo   Administrator-Modus aktiv – Scanner wird gestartet...
    echo.
    python main.py
) else (
    echo.
    echo   Starte als Administrator...
    echo.
    powershell -Command "Start-Process '%~dp0Start_scanner.bat' -Verb RunAs"
    exit
)

:: Optional: pause am Ende, falls du die Ausgabe sehen willst
:: Entferne die nächste Zeile, wenn das Fenster automatisch schließen soll nach dem Scan
pause