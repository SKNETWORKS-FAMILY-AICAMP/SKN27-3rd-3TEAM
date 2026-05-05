# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Pokémon-themed full-stack application featuring a Battle Simulator, AI Chatbot, Pokédex, and Team Builder. The backend is FastAPI, the frontend is Streamlit, and the database is PostgreSQL. AI features use LangChain with OpenAI and Groq.

## Running the Project

**Full stack (recommended):**
```bash
docker-compose up
```
- Frontend: http://localhost:8501
- Backend: http://localhost:8080

**Backend only (local dev):**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend only (local dev):**
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**Prerequisites:** Copy `.env.sample` to `.env` and fill in credentials before first run. The PostgreSQL container (`pokemon_db`) must exist and be attached to the `pokemon_db_collection_default` Docker network.

## Environment Variables

See `.env.sample` for required variables:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — PostgreSQL credentials
- `OPENAI_API_KEY` — OpenAI API key
- `GROQ_API_KEY` — Groq LLM API key
- `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` — LangSmith observability

## Architecture

### Services (docker-compose)
| Service | Internal host | Exposed port |
|---|---|---|
| `pokemon_backend` | `backend:8000` | `8080` |
| `pokemon_frontend` | `frontend:8501` | `8501` |
| `pokemon_db` | `pokemon_db:5432` | external |

The frontend reads `BACKEND_URL` (set in docker-compose) to reach the backend. Two Docker networks are used: `skn_net` (internal, frontend↔backend) and `pokemon_db_collection_default` (external, backend↔database).

### Backend (`backend/`)
FastAPI app in `main.py`. CORS is open to all origins. Database connection uses SQLAlchemy with `psycopg2`. LangChain/LangGraph orchestrate AI features using OpenAI and Groq models. Config is loaded via `python-dotenv`.

### Frontend (`frontend/`)
Streamlit multi-page app. `app.py` is the home/navigation page. Feature pages live alongside it:
- `battle.py` — Battle Simulator
- `chatbot.py` — AI Chatbot
- `pokedex.py` — Pokédex
- `teambuilding.py` — Team Builder
- `login.py` — Login

Pages call the backend via HTTP (`requests`). Session/cookie state uses `streamlit-cookies-controller`.

## Key Implementation Notes

- All frontend feature pages are currently stubs — only titles are rendered.
- Backend has only `GET /` and `GET /health` endpoints implemented.
- No test framework is configured. No linting config (ruff, flake8, etc.) is present.
- When adding new backend routes, add them to `backend/main.py` (or a router mounted there).
- When adding new frontend pages, create a `.py` file in `frontend/` and add a navigation button in `app.py`.
