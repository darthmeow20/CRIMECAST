@echo off
REM CRIMECAST — weekly / daily NEW-news refresh (Tier-3)
REM Run manually, or register with Windows Task Scheduler (see docs/TIER3_OPS.md)
cd /d "%~dp0"

set "PY="
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if not defined PY if exist "%~dp0..\env\Scripts\python.exe" set "PY=%~dp0..\env\Scripts\python.exe"
if not defined PY if exist "C:\Python311\python.exe" set "PY=C:\Python311\python.exe"
if not defined PY set "PY=python"

echo [%DATE% %TIME%] CRIMECAST news refresh starting...
"%PY%" -B "%~dp0acquire_news_signals.py" --refresh-new --max-items 22
echo [%DATE% %TIME%] Exit code %ERRORLEVEL%
exit /b %ERRORLEVEL%
