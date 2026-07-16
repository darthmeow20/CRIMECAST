@echo off
REM Flatten all markdown into docs\ (no subfolders for .md)
cd /d "%~dp0"

echo === Flattening docs subfolders into docs\ ===

if exist "docs\guides\*.md" copy /Y "docs\guides\*.md" "docs\" >nul
if exist "docs\sentiment\*.md" copy /Y "docs\sentiment\*.md" "docs\" >nul
if exist "docs\status\*.md" copy /Y "docs\status\*.md" "docs\" >nul
if exist "docs\rape_2026\*.md" copy /Y "docs\rape_2026\*.md" "docs\" >nul
if exist "docs\diagrams\*.mmd" copy /Y "docs\diagrams\*.mmd" "docs\" >nul

echo === Copying report / model markdown into docs\ ===

if exist "report_materials\data_flow_diagram.md" copy /Y "report_materials\data_flow_diagram.md" "docs\data_flow_diagram.md" >nul
if exist "report_materials\dfd_level_0.md" copy /Y "report_materials\dfd_level_0.md" "docs\dfd_level_0.md" >nul
if exist "report_materials\dfd_level_1.md" copy /Y "report_materials\dfd_level_1.md" "docs\dfd_level_1.md" >nul
if exist "report_materials\partial_report.md" copy /Y "report_materials\partial_report.md" "docs\partial_report.md" >nul
if exist "report_materials\screenshots.md" copy /Y "report_materials\screenshots.md" "docs\screenshots.md" >nul
if exist "report_materials\system_flow_diagram.md" copy /Y "report_materials\system_flow_diagram.md" "docs\system_flow_diagram.md" >nul
if exist "report_materials\README.md" copy /Y "report_materials\README.md" "docs\REPORT_MATERIALS_README.md" >nul
if exist "reports\CRIMECAST_PARTIAL_REPORT.md" copy /Y "reports\CRIMECAST_PARTIAL_REPORT.md" "docs\CRIMECAST_PARTIAL_REPORT.md" >nul
if exist "reports\screenshots\README.md" copy /Y "reports\screenshots\README.md" "docs\REPORTS_SCREENSHOTS_README.md" >nul
if exist "dataset\cleaned\data_quality_report.md" copy /Y "dataset\cleaned\data_quality_report.md" "docs\data_quality_report.md" >nul
if exist "model_outputs\training_report.md" copy /Y "model_outputs\training_report.md" "docs\training_report.md" >nul
if exist "model_outputs\figures\visual_report.md" copy /Y "model_outputs\figures\visual_report.md" "docs\visual_report.md" >nul

echo === Removing emptied docs subfolder files ===

del /q "docs\guides\*.md" 2>nul
del /q "docs\sentiment\*.md" 2>nul
del /q "docs\status\*.md" 2>nul
del /q "docs\rape_2026\*.md" 2>nul
del /q "docs\diagrams\*.mmd" 2>nul
rd "docs\guides" 2>nul
rd "docs\sentiment" 2>nul
rd "docs\status" 2>nul
rd "docs\rape_2026" 2>nul
rd "docs\diagrams" 2>nul

echo.
echo Done. Markdown is flat under docs\
echo Then run CLEANUP_ROOT.bat to remove root stubs + empty docs subdirs.
echo Or: python _flatten_docs.py
echo.
pause
