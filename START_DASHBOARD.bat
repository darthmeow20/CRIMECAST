@echo off
cd /d "%~dp0"
echo.
echo  CRIMECAST dashboard
echo  %CD%
echo.
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8501" ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul
if exist "__pycache__\crimecast_ui*.pyc" del /q "__pycache__\crimecast_ui*.pyc" 2>nul
if exist "__pycache__\dashboard*.pyc" del /q "__pycache__\dashboard*.pyc" 2>nul
echo  Starting: streamlit run dashboard.py
echo  Browser: http://localhost:8501
echo.
if exist ".venv\Scripts\streamlit.exe" (
  ".venv\Scripts\streamlit.exe" run "%~dp0dashboard.py" --server.port 8501
) else (
  py -3 -m streamlit run "%~dp0dashboard.py" --server.port 8501
)
pause
