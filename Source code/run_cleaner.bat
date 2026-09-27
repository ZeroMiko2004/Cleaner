@echo off
chcp 65001 >nul
cd /d "%~dp0"
python cleaner.py
echo.
pause
