@echo off
cd /d "%~dp0"
python -m fg
if errorlevel 1 pause
