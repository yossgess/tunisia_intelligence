@echo off
REM Batch Enrichment Runner for Tunisia Intelligence MVP
REM This script helps you run batch enrichment easily on Windows

echo ========================================
echo Tunisia Intelligence - Batch Enrichment
echo ========================================

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
)

REM Check if user provided arguments
if "%1"=="" (
    echo Usage examples:
    echo   run_batch_enrichment.bat status
    echo   run_batch_enrichment.bat test  
    echo   run_batch_enrichment.bat articles --limit 20
    echo   run_batch_enrichment.bat posts --limit 10
    echo.
    echo Running status check...
    python batch_enrich_mvp.py status
) else (
    echo Running: python batch_enrich_mvp.py %*
    python batch_enrich_mvp.py %*
)

echo.
echo ========================================
echo Batch enrichment completed
echo ========================================
pause
