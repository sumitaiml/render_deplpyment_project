#!/usr/bin/env powershell
<#
.SYNOPSIS
    Stop the HRTech Platform Backend Server
.DESCRIPTION
    This script stops all running FastAPI/Uvicorn backend servers on port 8000.
.EXAMPLE
    .\stop-platform.ps1
#>

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "         HRTech Platform - Stopping Application" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[*] Searching for running backend processes..." -ForegroundColor Yellow

# Find processes using port 8000
$processesKilled = 0

try {
    # Method 1: Find by port
    $connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "   [WARNING] Stopping: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                $processesKilled++
            }
        }
    }
} catch {
    # Silently continue if method fails
}

# Method 2: Find Python processes running uvicorn
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
foreach ($proc in $pythonProcesses) {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
        if ($cmdLine -like "*uvicorn*app.main:app*") {
            Write-Host "   [WARNING] Stopping: Python/Uvicorn (PID: $($proc.Id))" -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            $processesKilled++
        }
    } catch {
        # Continue to next process
    }
}

Start-Sleep -Milliseconds 500

if ($processesKilled -gt 0) {
    Write-Host ""
    Write-Host "[OK] Successfully stopped $processesKilled process(es)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[INFO] No running backend processes found" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "            HRTech Platform has been stopped" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the platform again, run: .\start-platform.ps1" -ForegroundColor Cyan
Write-Host ""

# Brief pause so user can see the message
Start-Sleep -Seconds 2
