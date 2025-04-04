@echo off
REM Setup script for Mimir's Bucket MCP Server on Windows

echo Setting up Mimir's Bucket environment...

REM Check if UV is installed
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo UV package manager not found, installing...
    powershell -ExecutionPolicy Bypass -Command "iwr https://astral.sh/uv/install.ps1 -useb | iex"
    if %ERRORLEVEL% neq 0 (
        echo Failed to install UV. Please install manually and try again.
        exit /b 1
    )
)

REM Create virtual environment
echo Creating virtual environment...
uv venv
if %ERRORLEVEL% neq 0 (
    echo Failed to create virtual environment
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
uv add "mcp[cli]" python-arango python-dotenv numpy
uv add -o sentence-transformers

REM Install the package in development mode
echo Installing package in development mode...
uv pip install -e .

echo Setup complete!
echo.
echo To use Mimir's Bucket:
echo 1. Run "main.py" to start the MCP server
echo 2. Or use "scripts\update_embeddings.py" to update document embeddings
echo.

REM Keep console open
pause
