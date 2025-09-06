@echo off
REM Change directory to the folder where manage.py is located
cd /d %~dp0

REM Activate virtual environment (adjust path if different)
call venv\Scripts\activate

REM Start Django server in background
start cmd /k "python manage.py runserver"

REM Wait a bit for server to start
timeout /t 3 >nul

REM Open default browser at localhost:8000
start http://127.0.0.1:8000
