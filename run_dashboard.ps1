# Tunisia Intelligence Dashboard Runner (PowerShell)
# Enhanced dashboard with pipeline tabs and Facebook configuration

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Tunisia Intelligence Dashboard" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Features Available:" -ForegroundColor Green
Write-Host "  • Pipeline Tabs (RSS, Facebook, AI, Vectorization)" -ForegroundColor White
Write-Host "  • Facebook Configuration Interface" -ForegroundColor White
Write-Host "  • Real-time System Monitoring" -ForegroundColor White
Write-Host "  • Interactive Controls" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Dashboard URL: http://localhost:5000" -ForegroundColor Magenta
Write-Host " Press Ctrl+C to stop" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists and activate it
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Check if dashboard directory exists
if (-not (Test-Path "web_dashboard")) {
    Write-Host "Error: web_dashboard directory not found!" -ForegroundColor Red
    Write-Host "Please ensure you're running this from the project root directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if app.py exists
if (-not (Test-Path "web_dashboard\app.py")) {
    Write-Host "Error: Dashboard app.py not found!" -ForegroundColor Red
    Write-Host "Expected: web_dashboard\app.py" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    # Change to dashboard directory and run
    Set-Location "web_dashboard"
    Write-Host "Starting dashboard..." -ForegroundColor Green
    python app.py
}
catch {
    Write-Host "Error running dashboard: $_" -ForegroundColor Red
}
finally {
    # Return to original directory
    Set-Location ".."
    Write-Host ""
    Write-Host "Dashboard stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}
