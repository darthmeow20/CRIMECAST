@echo off
cd /d "%~dp0"
echo.
echo  === CRIMECAST: kill old Streamlit + prove file is fixed ===
echo  Directory: %CD%
echo.

echo  [A] Searching dashboard.py for broken ticker text...
findstr /N /C:"Models {n_models}" /C:"LIVE WIRE" /C:"HIGH {open_alerts}" /C:"&nbsp; Models" dashboard.py
if %ERRORLEVEL%==0 (
  echo.
  echo  BAD: old ticker still in dashboard.py on DISK.
  echo  Close editor, discard changes, re-open file from this folder.
  pause
  exit /b 1
)
echo  GOOD: none of those bad strings are in dashboard.py
echo.

echo  [B] Kill ALL python/streamlit that might hold old code...
taskkill /F /IM streamlit.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8501 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8502 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul

echo  [C] Delete pycache...
if exist "__pycache__" rd /s /q "__pycache__"

echo  [D] Show BUILD_ID line from disk:
findstr /N "BUILD_ID" dashboard.py
echo.

echo  [E] Launch NEW process on port 8502 (not 8501)...
echo      Open browser:  http://localhost:8502
echo      Sidebar must show: build 20260719f-safe
echo      and path ending in CRIMECAST\dashboard.py
echo.
if exist ".venv\Scripts\streamlit.exe" (
  ".venv\Scripts\streamlit.exe" run "%~dp0run_crimecast.py" --server.port 8502 --server.headless true
) else (
  py -3 -m streamlit run "%~dp0run_crimecast.py" --server.port 8502
)
pause
