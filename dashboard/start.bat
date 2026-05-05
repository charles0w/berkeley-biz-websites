@echo off
cd /d "%~dp0"
pip install -r requirements.txt -q
echo.
echo  Dashboard starting at http://localhost:8080
echo  Press Ctrl+C to stop.
echo.
uvicorn server:app --reload --port 8080
