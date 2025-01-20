@echo off
set BACKUP_LOG=C:\Users\PCAdmin\Desktop\Desktop\CS Projects\ChessMate\logs\backup.log

REM Create logs directory if it doesn't exist
if not exist "%~dp0..\..\logs" mkdir "%~dp0..\..\logs"

REM Activate virtual environment if exists
if exist "%~dp0..\.venv\Scripts\activate.bat" (
    call "%~dp0..\.venv\Scripts\activate.bat"
)

REM Run backup script
python "%~dp0backup_db.py" >> "%BACKUP_LOG%" 2>&1

REM Deactivate virtual environment
if exist "%~dp0..\.venv\Scripts\deactivate.bat" (
    call "%~dp0..\.venv\Scripts\deactivate.bat"
) 