#!/usr/bin/env powershell
<#
.SYNOPSIS
    Start the HRTech Platform (Backend + Frontend)
.DESCRIPTION
    This script starts the FastAPI backend server and opens the frontend in your default browser.
    Works from any location - no need to change directories!
.EXAMPLE
    .\start-platform.ps1
#>

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendFile = Join-Path $ScriptDir "index.html"
$ProjectRoot = Split-Path -Parent $ScriptDir

# Prefer project virtual environment Python, fallback to PATH python
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonExe = "python"
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "         HRTech Platform - Starting Application" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend directory exists
if (-not (Test-Path $BackendDir)) {
    Write-Host "[ERROR] Backend directory not found at: $BackendDir" -ForegroundColor Red
    Write-Host "   Please make sure you're running this script from the hrtech-platform folder." -ForegroundColor Yellow
    pause
    exit 1
}

# Check if frontend file exists
if (-not (Test-Path $FrontendFile)) {
    Write-Host "[ERROR] Frontend file not found at: $FrontendFile" -ForegroundColor Red
    Write-Host "   Please make sure index.html exists in the hrtech-platform folder." -ForegroundColor Yellow
    pause
    exit 1
}

# Check if Python is installed
try {
    $pythonVersion = & $PythonExe --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
    if ($PythonExe -ne "python") {
        Write-Host "[OK] Using virtual environment: $PythonExe" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "   Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""
Write-Host "[*] Starting Backend Server..." -ForegroundColor Yellow

# Kill any existing uvicorn processes on port 8000
$existingProcess = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($existingProcess) {
    Write-Host "[WARNING] Port 8000 is already in use. Attempting to free it..." -ForegroundColor Yellow
    Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -like "*uvicorn*" -or $_.CommandLine -like "*uvicorn*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# Start the backend server in a new PowerShell window
$backendCommand = "cd '$BackendDir'; & '$PythonExe' -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -WindowStyle Normal

Write-Host "[OK] Backend server starting on http://localhost:8000" -ForegroundColor Green
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Wait for backend to start
Write-Host "[*] Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test if backend is responding
$maxRetries = 10
$retryCount = 0
$backendReady = $false

while (-not $backendReady -and $retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
        }
    } catch {
        $retryCount++
        Start-Sleep -Seconds 1
    }
}

if ($backendReady) {
    Write-Host "[OK] Backend is ready!" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Backend may still be initializing (this is normal)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[*] Opening Frontend..." -ForegroundColor Yellow

# Open the frontend in default browser
Start-Process $FrontendFile

Write-Host "[OK] Frontend opened in your default browser" -ForegroundColor Green
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "              HRTech Platform is Running!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend:     $FrontendFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "   - Upload resumes in the 'Upload Resume' tab" -ForegroundColor White
Write-Host "   - Create job postings in the 'Create Job' tab" -ForegroundColor White
Write-Host "   - Rank candidates in the 'Rank Candidates' tab" -ForegroundColor White
Write-Host "   - View results and explanations in the 'Results' tab" -ForegroundColor White
Write-Host ""
Write-Host "To stop the platform:" -ForegroundColor Red
Write-Host "   - Close the backend PowerShell window, or" -ForegroundColor White
Write-Host "   - Run: .\stop-platform.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to keep this window open for status monitoring..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
