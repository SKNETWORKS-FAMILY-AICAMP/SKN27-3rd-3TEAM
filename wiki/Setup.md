# Setup

---

## 사전 요구사항

- Docker Desktop (권장)
- 또는 Python 3.11+, PostgreSQL 16, Neo4j 5+

---

## 전체 스택 실행 (권장)

```bash
# 1. 환경 변수 설정
cp .env.sample .env
# .env 파일을 열어 아래 항목 입력

# 2. Docker Compose 빌드 & 실행
docker compose up --build
```

| 서비스 | URL |
|---|---|
| Frontend | http://localhost:8501 |
| Backend API Docs | http://localhost:8080/docs |
| Neo4j Browser | http://localhost:7474 |

---

## 로컬 개발

### 백엔드

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드

```bash
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

> PostgreSQL과 Neo4j 컨테이너는 별도로 실행되어 있어야 합니다.

---

## 환경 변수

`.env.sample`을 복사해 `.env`로 생성 후 아래 값들을 채웁니다.

```env
# ─── PostgreSQL ───────────────────────────────
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pokemon_db

# ─── LLM ──────────────────────────────────────
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...               # HuggingFace (임베딩 모델)

# ─── 웹 검색 ──────────────────────────────────
TAVILY_API_KEY=tvly-...

# ─── LangSmith (선택) ─────────────────────────
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=pokemon_world

# ─── Neo4j ────────────────────────────────────
NEO4J_AUTH=neo4j/password
NEO4J_URI=bolt://neo4j:7687

# ─── GitHub OAuth ─────────────────────────────
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=http://localhost:8501/login
```

### 필수 / 선택 구분

| 변수 | 필수 | 없으면 |
|---|---|---|
| `POSTGRES_*` | ✅ | DB 연결 실패 |
| `OPENAI_API_KEY` | ✅ | 팀 빌더 RAG · 챗봇 동작 불가 |
| `GROQ_API_KEY` | ✅ | Gemma 모델 선택 불가 |
| `HF_TOKEN` | ✅ | 임베딩 모델 로드 실패 |
| `TAVILY_API_KEY` | ✅ | 웹 검색 툴 동작 불가 |
| `NEO4J_AUTH` | ✅ | 팀 빌더 · 그래프 검색 불가 |
| `GITHUB_CLIENT_ID/SECRET` | ✅ | 로그인 불가 |
| `LANGSMITH_*` | 선택 | LLM 트레이싱 비활성화 |

---

## 데이터 초기화

### PostgreSQL 스키마

Docker Compose 첫 실행 시 `backend/main.py`에서 SQLAlchemy로 테이블을 자동 생성합니다.  
수동 초기화가 필요하면:

```bash
psql -h localhost -U postgres -d pokemon_db -f database/postgre/utils/schema.sql
```

### Neo4j 데이터 로드

```bash
cd database/graph/neo4j
python db_loader.py
```

포켓몬 · 타입 · 특성 · 기술 · 진화 체인 · 타입 상성 관계를 Neo4j에 적재합니다.
