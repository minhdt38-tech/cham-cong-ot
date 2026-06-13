@echo off
cd /d "%~dp0"

echo Dang khoi dong Cham Cong OT...
echo.

py server.py
if errorlevel 1 (
    python server.py
    if errorlevel 1 (
        echo.
        echo LOI: Khong chay duoc Python.
        echo Hay mo CMD va chay lenh: py server.py
        pause
    )
)
