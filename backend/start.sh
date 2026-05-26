#!/bin/bash
# AI Compiler Backend Startup
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  python -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example - set OPENAI_API_KEY"
fi

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
