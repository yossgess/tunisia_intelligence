@echo off
REM Tunisia Intelligence Dashboard Runner (Windows Batch)
REM Simple script to launch the enhanced dashboard with pipeline tabs and Facebook configuration

echo.
echo ========================================
echo  Tunisia Intelligence Dashboard
echo ========================================
echo  Features Available:
echo  - Pipeline Tabs (RSS, Facebook, AI, Vectorization)
echo  - Facebook Configuration Interface  
echo  - Real-time System Monitoring
echo  - Interactive Controls
echo ========================================
echo  Dashboard URL: http://localhost:5000
echo  Press Ctrl+C to stop
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Change to dashboard directory and run
cd web_dashboard
python app.py

pause
