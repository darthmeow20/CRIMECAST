@echo off
cd /d "%~dp0"
echo.
echo  CRIMECAST — migrate CSVs into SQLite (data\crimecast.db)
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" migrate_csv_to_db.py
) else (
  py -3 migrate_csv_to_db.py
)
echo.
pause
