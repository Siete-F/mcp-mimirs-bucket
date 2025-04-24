@echo off
SETLOCAL

echo Mimir's Bucket - Setup Script

REM Check if Python is installed
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%V in ('python -c "import sys; print(sys.version.split()[0])"') do set PYTHON_VERSION=%%V
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python version %PYTHON_VERSION% is not supported.
    echo Please install Python 3.10 or higher.
    exit /b 1
)

if %PYTHON_MAJOR%==3 (
    if %PYTHON_MINOR% LSS 10 (
        echo Error: Python version %PYTHON_VERSION% is not supported.
        echo Please install Python 3.10 or higher.
        exit /b 1
    )
)

echo Python %PYTHON_VERSION% detected.

REM Check if UV is installed and install if needed
where uv >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo UV not found. Installing UV...
    powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression"
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install UV.
        exit /b 1
    )
    echo UV installed successfully.
) ELSE (
    echo UV already installed.
)

REM Create and activate virtual environment
if not exist .venv (
    echo Creating virtual environment...
    uv venv
) else (
    echo Virtual environment already exists.
)

echo Installing dependencies...
call uv pip install --upgrade "mcp[cli]"
call uv pip install python-arango
call uv pip install python-dotenv
call uv pip install sentence-transformers
call uv pip install httpx

echo Setup completed successfully.
echo ===================================
echo To use Mimir's Bucket:
echo - Ensure ArangoDB is running
echo - Create a .env file with database credentials (check README.md)
echo - Run with: python main.py
echo - Or install with Claude Desktop: mcp install main.py -n "Mimir's Bucket"
echo ===================================

ENDLOCAL
