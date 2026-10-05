@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py %*
) else (
  echo Bitte zuerst die Installation aus README.md ausfuehren.
  echo Es wird eine lokale virtuelle Python-Umgebung .venv benoetigt.
  exit /b 2
)
if errorlevel 1 pause
