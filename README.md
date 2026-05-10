# SKN27-3rd-3TEAM — Pokémon AI Assistant

> SKN 27기 3조 | LLM, 너로 정했다! — 포켓몬 테마 풀스택 AI 웹 애플리케이션

---

## 목차

1. [프로젝트 소개](#프로젝트-소개)
2. [팀원](#팀원)
3. [기술 스택](#기술-스택)
4. [서비스 아키텍처](#서비스-아키텍처)
5. [페이지 구성](#페이지-구성)
6. [데이터 수집 파이프라인](#데이터-수집-파이프라인)
7. [실행 방법](#실행-방법)
8. [환경 변수](#환경-변수)
9. [프로젝트 구조](#프로젝트-구조)

---

## 프로젝트 소개

PokeAPI 기반의 포켓몬 데이터를 수집·정제하여 PostgreSQL(pgvector) + Neo4j 지식 베이스를 구축하고,  
LangChain / LangGraph로 RAG 파이프라인을 연결한 **포켓몬 AI 어시스턴트**입니다.

- **전국 포켓몬 도감** — 1세대~최신 세대, 종족값·타입·진화 트리 검색
- **배틀 시뮬레이터** — 상성 분석 + 정밀 데미지 계산
- **AI 포켓몬 박사 챗봇** — RAG 기반 실시간 Q&A
- **팀 빌더** — 6인 파티 약점·방어 상성 시각화

---

## 팀원

<table>
  <tr>
    <td align="center" width="160">
      <img src="docs/images/team/1.png" width="100" height="100" style="border-radius:50%; object-fit:cover;" alt="1"><br><br>
      <b>1</b><br>
      <sub>역할</sub>
    </td>
    <td align="center" width="160">
      <img src="docs/images/team/2.png" width="100" height="100" style="border-radius:50%; object-fit:cover;" alt="2"><br><br>
      <b>2</b><br>
      <sub>역할</sub>
    </td>
    <td align="center" width="160">
      <img src="docs/images/team/3.png" width="100" height="100" style="border-radius:50%; object-fit:cover;" alt="3"><br><br>
      <b>3</b><br>
      <sub>역할</sub>
    </td>
    <td align="center" width="160">
      <img src="docs/images/team/4.png" width="100" height="100" style="border-radius:50%; object-fit:cover;" alt="4"><br><br>
      <b>4</b><br>
      <sub>역할</sub>
    </td>
    <td align="center" width="160">
      <img src="docs/images/team/5.png" width="100" height="100" style="border-radius:50%; object-fit:cover;" alt="5"><br><br>
      <b>5</b><br>
      <sub>역할</sub>
    </td>
  </tr>
</table>

---

## 기술 스택

### Backend

| 분류 | 라이브러리 | 버전 |
|------|-----------|------|
| Web Framework | FastAPI | 0.136.1 |
| ASGI Server | Uvicorn | 0.46.0 |
| Data Validation | Pydantic | (FastAPI 내장) |
| ORM | SQLAlchemy | 2.0.49 |
| DB Driver | psycopg2-binary | 2.9.12 |
| Vector Extension | pgvector | 0.4.2 |
| Graph DB Client | neo4j | 5.28.2 |
| Graph Data Science | graphdatascience | 1.17 |

### AI / LLM

| 분류 | 라이브러리 |
|------|-----------|
| LLM Orchestration | LangChain, LangChain-Core |
| OpenAI 연동 | LangChain-OpenAI, openai |
| Groq 연동 | LangChain-Groq, groq |
| Agent Framework | LangGraph |
| Web Search Tool | tavily-python |
| Observability | LangSmith |

### Frontend

| 분류 | 라이브러리 | 버전 |
|------|-----------|------|
| UI Framework | Streamlit | 1.57.0 |
| HTTP Client | requests | 2.33.1 |
| 쿠키/세션 | streamlit-cookies-controller | 0.0.4 |

### Database & Infrastructure

| 분류 | 기술 | 버전/이미지 |
|------|------|------------|
| RDBMS | PostgreSQL + pgvector | `pgvector/pgvector:pg16` |
| Graph DB | Neo4j (APOC + GDS 플러그인) | `neo4j:latest` |
| Container | Docker & Docker Compose | — |

---

## 서비스 아키텍처

```
[사용자 브라우저]
       │
       ▼
[Streamlit Frontend] :8501
       │  HTTP (BACKEND_URL)
       ▼
[FastAPI Backend]    :8000 (외부 포트 8080)
       │
       ├──► [PostgreSQL + pgvector] :5432 (외부 포트 5433)
       │         RAG 벡터 검색, 포켓몬 정형 데이터
       │
       └──► [Neo4j]                 :7687 Bolt / :7474 HTTP
                 그래프 기반 관계 데이터 (진화 트리, 타입 상성)
```

**Docker 네트워크:** `skn_net` (내부 서비스 간 통신)

---

## 페이지 구성

### 메인 (랜딩)
- 파일: [frontend/app.py](frontend/app.py)
- 풀스크린 스크롤 스냅 랜딩 페이지
- 각 기능(도감 / 배틀 / 챗봇 / 팀빌더)으로 네비게이션
- 포켓몬 공식 아트워크 + 애니메이션 효과

### 포켓덱스
- 파일: [frontend/pages/pokedex.py](frontend/pages/pokedex.py)
- 전국 포켓몬 카드 목록 (1세대~팔데아)
- 타입 필터링, 이름/번호 검색, 지역별 필터
- 백엔드 API: `GET /api/v1/pokemon/`

### 포켓몬 상세
- 파일: [frontend/pages/pokemon_detail.py](frontend/pages/pokemon_detail.py)
- 종족값 레이더 차트, 타입 배지, 도감 설명
- 진화 트리 시각화
- 백엔드 API: `GET /api/v1/pokemon/{id}`

### 배틀 시뮬레이터
- 파일: [frontend/pages/battle.py](frontend/pages/battle.py)
- 포켓몬 1:1 배틀 시뮬레이션
- 타입 상성 분석 + 데미지 계산

### AI 포켓몬 박사 챗봇
- 파일: [frontend/pages/chatbot.py](frontend/pages/chatbot.py)
- RAG 기반 포켓몬 Q&A 챗봇
- LangChain + Groq/OpenAI LLM 연동

### 팀 빌더
- 파일: [frontend/pages/teambuilding.py](frontend/pages/teambuilding.py)
- 최대 6마리 파티 구성
- 타입 방어 상성 시각화 및 약점 분석

### 로그인
- 파일: [frontend/pages/login.py](frontend/pages/login.py)
- 사용자 인증 페이지

---

## 데이터 수집 파이프라인

PokeAPI를 활용한 포켓몬 데이터 수집·정제·적재 파이프라인입니다.  
자세한 내용은 **[database/common/README.md](database/common/README.md)** 를 참조하세요.

### 파이프라인 요약

```
PokeAPI
  │
  ▼ Step 1. 수집 (api_collector.py)
data/raw/          ← 원본 JSON (~1025마리, 18타입, ~950기술, 등)
  │
  ▼ Step 2. 정제 (data_processor.py)
data/processed/    ← 한국어 필터링, DB 스키마 매핑
  │
  ▼ Step 3. 적재 (db_loader.py)
PostgreSQL         ← ON CONFLICT DO UPDATE 멱등성 보장
  │
  ▼ Step 4. 벡터화 (vectorizer.py)
flavor_text.embedding, moves.embedding  ← OpenAI 임베딩
```

**수집 대상:** 포켓몬 ~1025마리, 속성 18개, 기술 ~950개, 도구 ~2250개, 특성 ~307개, 성격 25개, 진화 트리 ~550개

---

## 실행 방법

### 전체 스택 (권장)

```bash
# .env 파일 먼저 준비 (.env.sample 복사 후 수정)
cp .env.sample .env

docker-compose up
```

| 서비스 | 접속 주소 |
|--------|----------|
| Frontend (Streamlit) | http://localhost:8501 |
| Backend (FastAPI Swagger) | http://localhost:8080/docs |
| Neo4j Browser | http://localhost:7474 |
| PostgreSQL | localhost:5433 |

### 로컬 개발 (Backend)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 로컬 개발 (Frontend)

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 환경 변수

`.env.sample`을 복사하여 `.env`를 생성하세요.

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pokemon_db
POSTGRES_PORT=5433

# Neo4j
NEO4J_AUTH=neo4j/password

# AI API Keys
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# LangSmith (선택)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=pokemon-ai
```

---

## 프로젝트 구조

```
SKN27-3rd-3TEAM/
├── backend/                    # FastAPI 백엔드
│   ├── main.py                 # 앱 진입점, 라우터 등록
│   ├── database.py             # SQLAlchemy 연결 설정
│   ├── models.py               # ORM 모델
│   ├── schemas.py              # Pydantic 스키마
│   ├── crud.py                 # DB 쿼리 함수
│   ├── routers/
│   │   └── pokemon.py          # /api/v1/pokemon 라우터
│   └── graph/
│       └── neo4j_client.py     # Neo4j 연결 클라이언트
│
├── frontend/                   # Streamlit 프론트엔드
│   ├── app.py                  # 메인 랜딩 페이지
│   ├── pages/
│   │   ├── pokedex.py          # 전국 포켓몬 도감
│   │   ├── pokemon_detail.py   # 포켓몬 상세 페이지
│   │   ├── battle.py           # 배틀 시뮬레이터
│   │   ├── chatbot.py          # AI 챗봇
│   │   ├── teambuilding.py     # 팀 빌더
│   │   ├── login.py            # 로그인
│   │   └── style/              # 페이지별 CSS 스타일
│   └── utils/
│       └── ui.py               # 공통 UI 컴포넌트 (헤더 등)
│
├── database/
│   ├── common/                 # 공통 데이터 수집 파이프라인
│   │   ├── README.md           # 파이프라인 상세 문서
│   │   └── processing/
│   │       ├── api_collector.py
│   │       ├── data_processor.py
│   │       └── scheduler.py
│   ├── postgre/                # PostgreSQL 관련
│   │   ├── utils/
│   │   │   ├── schema.sql      # DB 스키마 (pgvector 포함)
│   │   │   ├── db_loader.py    # DB 적재 스크립트
│   │   │   └── vectorizer.py   # OpenAI 임베딩 생성
│   │   └── main_pipeline.py    # 통합 실행 파이프라인
│   └── graph/
│       └── graph_loader.py     # Neo4j 데이터 적재
│
├── docs/                       # 추가 문서
├── docker-compose.yml          # 전체 스택 컨테이너 정의
├── requirements.txt            # Python 의존성
├── .env.sample                 # 환경 변수 샘플
└── README.md
```

---

## Backend API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 루트 (상태 확인) |
| GET | `/health` | 헬스체크 |
| GET | `/api/v1/pokemon/` | 포켓몬 목록 (검색·타입·지역 필터, 페이지네이션) |
| GET | `/api/v1/pokemon/abilities` | 전체 특성 목록 |
| GET | `/api/v1/pokemon/{id}` | 포켓몬 상세 (스탯, 진화, 도감 설명) |

Swagger UI: http://localhost:8080/docs

---

© 2026 SKN 27기 3조 · Powered by Advanced AI
