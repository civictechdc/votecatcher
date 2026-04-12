@echo off
echo === VoteCatcher Setup ===

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed.
    echo Install it from https://www.docker.com/products/docker-desktop/
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running. Please open Docker Desktop first.
    exit /b 1
)

if not exist backend\.env.local (
    copy backend\.env.example backend\.env.local
    echo Created backend\.env.local
)

if not exist frontend\.env (
    copy frontend\.env.example frontend\.env
    echo Created frontend\.env
)

echo Starting VoteCatcher...
echo   App:  http://localhost:5173
echo   API:  http://localhost:8080/docs
echo.
echo Press Ctrl+C to stop.
echo.

docker compose up --build
