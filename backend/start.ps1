# AI Compiler Backend Startup (Windows)
Set-Location $PSScriptRoot

if (-not (Test-Path "venv")) {
    python -m venv venv
}
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt -q

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - set OPENAI_API_KEY"
}

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
