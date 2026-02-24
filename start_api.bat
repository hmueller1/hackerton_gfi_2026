@echo off
cd /d "%~dp0"
echo Starte BPU Pipeline API auf http://localhost:8000 ...
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
