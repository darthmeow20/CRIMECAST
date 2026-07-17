@echo off
cd /d "%~dp0"
echo.
echo  CRIMECAST — health check then dashboard
echo.
py -3 health_check.py 2>nul
if errorlevel 1 python health_check.py 2>nul
echo.
echo  Starting Streamlit dashboard...
echo  (close this window to stop)
echo.
py -3 -m streamlit run dashboard.py 2>nul
if errorlevel 1 python -m streamlit run dashboard.py
pause
