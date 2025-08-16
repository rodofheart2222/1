@echo off
echo ========================================
echo MT5 Dashboard System Startup
echo ========================================

REM Kill existing processes on common ports
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :80') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8765') do taskkill /f /pid %%a >nul 2>&1

REM Kill Node.js processes
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im npm.exe >nul 2>&1

echo Cleanup completed.
timeout /t 2 >nul

REM Try the advanced runner first
echo Attempting to start full system...
python run_full_system.py
if %errorlevel% neq 0 (
    echo Advanced runner failed, trying simple runner...
    python run_system_simple.py
)

pause