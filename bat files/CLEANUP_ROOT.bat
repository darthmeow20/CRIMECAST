@echo off
REM Deletes leftover stubs after docs flatten (flat docs/ only; keep root README.md)
cd /d "%~dp0"

echo Cleaning root stubs, junk py, and empty docs subfolders...

del /q "_gen_rape_csv.py" 2>nul
del /q "test1.py" 2>nul
del /q "rape_2026_engine.py" 2>nul
del /q "run_rape_2026_prediction.py" 2>nul
del /q "IMPORTANT_READ_ME_OPTION7.txt" 2>nul
del /q "Untitled-1.mmd" 2>nul

REM Root markdown stubs (keep README.md!)
del /q "QUICK_START.md" 2>nul
del /q "INSTALL_GUIDE.md" 2>nul
del /q "PROJECT_GUIDE.md" 2>nul
del /q "DASHBOARD_README.md" 2>nul
del /q "EXTERNAL_DATA_GUIDE.md" 2>nul
del /q "NEWS_SOURCES.md" 2>nul
del /q "DISTILBERT_GUIDE.md" 2>nul
del /q "SUBMISSION_CHECKLIST.md" 2>nul

del /q "SENTIMENT_GUIDE.md" 2>nul
del /q "SENTIMENT_IMPLEMENTATION.md" 2>nul
del /q "SENTIMENT_QUICK_REF.md" 2>nul
del /q "SENTIMENT_STATE_ANALYSIS.md" 2>nul
del /q "SENTIMENT_TN_DISTRICTS.md" 2>nul

del /q "PROJECT_STATUS.md" 2>nul
del /q "FULL_STATUS_CHECK.md" 2>nul
del /q "STATUS_SUMMARY.md" 2>nul
del /q "VERIFICATION_REPORT.md" 2>nul
del /q "PARTIAL_PROJECT_REPORT.md" 2>nul

del /q "RAPE_2026_IMPLEMENTATION.md" 2>nul
del /q "RAPE_2026_PREDICTIONS_GUIDE.md" 2>nul

del /q "flowchart LR.mmd" 2>nul
del /q "flowchart TB.mmd" 2>nul

REM Tests live under tests\ — remove root copies if present
del /q "test_project.py" 2>nul
del /q "test_option7_fix.py" 2>nul
del /q "_flatten_docs.py" 2>nul

REM Nested docs subfolders (after FLATTEN_DOCS.bat / _flatten_docs.py copied content)
if exist "docs\guides\" (
  del /q "docs\guides\*.md" 2>nul
  rd "docs\guides" 2>nul
)
if exist "docs\sentiment\" (
  del /q "docs\sentiment\*.md" 2>nul
  rd "docs\sentiment" 2>nul
)
if exist "docs\status\" (
  del /q "docs\status\*.md" 2>nul
  rd "docs\status" 2>nul
)
if exist "docs\rape_2026\" (
  del /q "docs\rape_2026\*.md" 2>nul
  rd "docs\rape_2026" 2>nul
)
if exist "docs\diagrams\" (
  del /q "docs\diagrams\*.mmd" 2>nul
  del /q "docs\diagrams\*.md" 2>nul
  rd "docs\diagrams" 2>nul
)

echo.
echo Done.
echo   Keep: app.py dashboard.py main.py clean_data train_model predict*
echo         sentiment* visualize* nlp acquire tn_map requirements README RUN_OPTION7
echo   Docs: docs\  (flat .md only)
echo   Tests: tests\
echo.
echo You can delete CLEANUP_ROOT.bat / FLATTEN_DOCS.bat after both run successfully.
echo.
pause
