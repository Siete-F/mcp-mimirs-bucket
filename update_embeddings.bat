@echo off
REM This batch file updates embeddings for all documents in the knowledge base

echo Updating embeddings in the knowledge base...
REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found at .venv. Please create it or modify this script.
    exit /b 1
)

REM Run the update script
python update_embeddings.py %*

REM Deactivate virtual environment
call deactivate

echo Embedding update complete!
