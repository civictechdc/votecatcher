$ErrorActionPreference = "Stop"

Write-Host "=== VoteCatcher Setup ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed." -ForegroundColor Red
    Write-Host "Install it from https://www.docker.com/products/docker-desktop/"
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please open Docker Desktop first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "backend\.env.local")) {
    Copy-Item "backend\.env.example" "backend\.env.local"
    Write-Host "Created backend\.env.local"
}

if (-not (Test-Path "frontend\.env")) {
    Copy-Item "frontend\.env.example" "frontend\.env"
    Write-Host "Created frontend\.env"
}

Write-Host ""
Write-Host "Starting VoteCatcher..." -ForegroundColor Green
Write-Host "  App:  http://localhost:5173"
Write-Host "  API:  http://localhost:8080/docs"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

docker compose up --build
