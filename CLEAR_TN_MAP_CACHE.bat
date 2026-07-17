@echo off
REM Clear stale tn_map bytecode so Streamlit picks up plot_tn_compare_districts
cd /d "%~dp0"
if exist "__pycache__\tn_map.cpython-*.pyc" del /q "__pycache__\tn_map.cpython-*.pyc"
if exist "__pycache__\tn_map*.pyc" del /q "__pycache__\tn_map*.pyc"
echo Cleared tn_map cache. Restart Streamlit (START_DASHBOARD.bat).
pause
