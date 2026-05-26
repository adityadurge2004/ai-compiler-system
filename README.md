# AI Compiler System

A production-style **AI orchestration compiler** that converts natural language into validated, executable application configurations. This is **not** a chatbot or simple code generator — it is a modular multi-stage pipeline with validation, targeted repair, and runtime artifact generation.

```
Natural Language → Intent → Architecture → DB → API → UI → Auth → Validate → Repair → Runtime
```

## Architecture

| Stage | Output |
|-------|--------|
| 1. Intent Extraction | Structured intent JSON |
| 2. Architecture Planning | Entities, services, pages, flows |
| 3. Database Generator | Tables, fields, relations, indexes |
| 4. API Generator | Endpoints, methods, request/response schemas |
| 5. UI Generator | Pages, components, forms, API bindings |
| 6. Auth Generator | Roles, permissions, route protection |
| 7. Validation Engine | Cross-layer consistency report |
| 8. Repair Engine | Targeted regeneration of failing layers |
| 9. Runtime Generator | SQLite DDL, SQLAlchemy, FastAPI routes, React configs |

## Project Structure

```
project-root/
├── backend/          # FastAPI + Python pipeline
├── frontend/         # Next.js dashboard
├── evaluation/       # Datasets + metrics runner
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (optional — demo mode works without it)

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic pydantic-settings openai python-dotenv httpx
# Or: pip install -r requirements.txt
copy .env.example .env
# Edit .env — set OPENAI_API_KEY (optional OPENAI_BASE_URL for OpenRouter)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the startup script:

```powershell
cd backend
.\start.ps1
```

**Important:** Run uvicorn from the `backend/` folder (not project root).

### Frontend

```powershell
cd frontend
npm install
copy .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/generate` | Full pipeline compile |
| POST | `/api/validate` | Validate existing schemas |
| POST | `/api/repair` | Targeted repair of failing layers |
| GET | `/api/metrics` | Pipeline metrics |
| POST | `/api/evaluate` | Batch evaluation |

### Generate Example

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a CRM with login, dashboard, contacts, and Stripe payments."}'
```

## Configuration

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for all stages |
| `OPENAI_TEMPERATURE` | `0.1` | Low temp for determinism |
| `MAX_REPAIR_ITERATIONS` | `3` | Max repair loops |
| `CORS_ORIGINS` | `localhost:3000` | Allowed frontend origins |

### Frontend (`frontend/.env.local`)

| Variable | Default |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

## Validation Engine

Validates across five dimensions:

1. **JSON validity** — serializable, parseable outputs
2. **Missing fields** — required schema fields present
3. **Schema mismatch** — HTTP methods, empty tables
4. **Cross-layer consistency** — API↔DB, UI↔API, Auth↔API, Arch↔UI
5. **Logical inconsistencies** — auth without login page, payments without entities

## Repair Engine

Does **not** blindly retry full generation. Flow:

```
Validation Error → Error Classification → Targeted Regeneration → Revalidation
```

Only the failing layer is regenerated (e.g., API/DB mismatch → regenerate API only).

## Runtime Artifacts

Executable outputs generated after validation:

- **SQLite DDL** — `CREATE TABLE` statements with FKs and indexes
- **SQLAlchemy models** — Python ORM classes
- **FastAPI routes** — CRUD endpoint stubs
- **React form configs** — TypeScript app configuration

## Evaluation Framework

20 prompts (10 normal + 10 edge cases):

```powershell
# Start backend first, then:
cd evaluation/metrics
python run_evaluation.py --api http://localhost:8000 --dataset both --output ../results/eval.json
```

Tracks: success rate, latency, validation failures, repair count, estimated token cost.

## Deployment

### Frontend (Vercel)

1. Import `frontend/` directory
2. Set `NEXT_PUBLIC_API_URL` to your backend URL
3. Deploy

### Backend (Render / Railway)

1. Set root directory to `backend/`
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables from `.env.example`

See `render.yaml` for Render blueprint.

## Demo Mode

Without `OPENAI_API_KEY`, the system runs in **deterministic demo mode** using fallback schemas. Useful for development and UI testing without API costs.

## Design Principles

1. **Never** one giant generation prompt — each stage has its own modular prompt
2. **Pydantic everywhere** — strict typed schemas
3. **Always validate** — cross-layer checks before runtime
4. **Targeted repair** — fix only what failed
5. **Structured JSON errors** — all failures return typed error objects
6. **Low temperature** (0.1) — deterministic outputs

## License

MIT
