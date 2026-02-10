@echo off
echo Starting SkyOps AI...

:: Start Backend in a new window
echo Starting Backend (API)...
start "SkyOps Backend" cmd /k "python -m uvicorn api:app --reload --port 8000"

:: Wait for backend to initialize
timeout /t 3

:: Start Frontend
echo Starting Frontend (UI)...
python -m streamlit run ui.py
