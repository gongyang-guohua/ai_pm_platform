
# Script to start the Backend Server correctly
$ErrorActionPreference = "Stop"

Write-Host "Starting AI PM Platform Backend..." -ForegroundColor Green
Write-Host "Changing directory to backend..." -ForegroundColor Gray

# Change to the script's directory, then into backend
Set-Location -Path "$PSScriptRoot\backend"

# Set PYTHONPATH to verify we load local code
$env:PYTHONPATH = "$PSScriptRoot\backend"

# Run Uvicorn via uv
Write-Host "Running Uvicorn..." -ForegroundColor Gray
uv run uvicorn app.main:app --reload --port 8000
