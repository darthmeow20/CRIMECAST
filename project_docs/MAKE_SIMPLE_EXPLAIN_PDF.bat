@echo off
cd /d "%~dp0\.."
echo.
echo  CRIMECAST simple English explain PDF
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip install reportlab -q
  ".venv\Scripts\python.exe" project_docs\generate_simple_explain_pdf.py
) else (
  py -3 -m pip install reportlab -q
  py -3 project_docs\generate_simple_explain_pdf.py
)
echo.
echo  Open HTML and Ctrl+P - Save as PDF if needed:
echo    project_docs\CRIMECAST_SIMPLE_EXPLAIN.html
echo  PDF (if reportlab ok):
echo    project_docs\CRIMECAST_SIMPLE_EXPLAIN.pdf
echo.
start "" "%~dp0CRIMECAST_SIMPLE_EXPLAIN.html"
pause
