# ERD (Entity-Relationship Diagram)

**프로젝트명:** 포켓몬 AI 챗봇  
**문서 버전:** v1.1  
**작성일:** 2025-05-14  
**최종 수정:** 2025-05-14 (PGVector 자동 생성 테이블 추가)  
**대상 DB:** PostgreSQL 15 + pgvector

---

## 1. 포켓몬 도메인 ERD

```mermaid
erDiagram
    pokemon {
        int     id           PK  "포켓몬 고유 ID"
        text    name             "포켓몬 이름 (한글)"
        int     height           "키 (단위: dm)"
        int     weight           "몸무게 (단위: hg)"
        int     base_exp         "기본 경험치"
        text    image_url        "공식 이미지 URL"
        text    cry_url          "울음소리 URL"
        bool    is_default       "기본 폼 여부"
    }

    pokemon_stats {
        int     pokemon_id   FK  "pokemon.id 참조"
        int     hp               "체력"
        int     attack           "공격"
        int     defense          "방어"
        int     sp_attack        "특수공격"
        int     sp_defense       "특수방어"
        int     speed            "스피드"
    }

    types {
        int     id           PK  "타입 고유 ID"
        text    name             "타입명 (한글)"
    }

    pokemon_types {
        int     pokemon_id   FK  "pokemon.id 참조"
        int     type_id      FK  "types.id 참조"
        int     slot             "주 타입(1) / 서브 타입(2)"
    }

    species {
        int     id           PK  "종족 고유 ID"
        int     pokemon_id   FK  "pokemon.id 참조"
        int     generation       "등장 세대 (1~9)"
        int     capture_rate     "포획률 (0~255)"
    }

    flavor_text {
        int     id           PK  "도감 설명 고유 ID"
        int     species_id   FK  "species.id 참조"
        text    version_name     "게임 버전명 (예: 레드, 블루)"
        text    content          "도감 설명 텍스트"
        vector  embedding        "OpenAI 임베딩 벡터 (1536차원)"
    }

    pokemon        ||--||  pokemon_stats  : "스탯 (1:1)"
    pokemon        ||--|{  pokemon_types  : "타입 보유 (1:N)"
    types          ||--|{  pokemon_types  : "타입 소속 (1:N)"
    pokemon        ||--||  species        : "종족 정보 (1:1)"
    species        ||--|{  flavor_text    : "도감 설명 (1:N)"
```

---

## 2. PGVector 도메인 ERD (LangChain 자동 생성)

> `ingest.py` 실행 시 LangChain PGVector가 PostgreSQL 내에 자동으로 생성하는 테이블입니다.  
> DDL을 직접 작성하지 않으며, `PGVector(collection_name="flavor_text")` 초기화 시점에 생성됩니다.  
> `search_flavor_text` 툴이 이 테이블을 대상으로 벡터 유사도 검색을 수행합니다.

```mermaid
erDiagram
    langchain_pg_collection {
        uuid    uuid         PK  "컬렉션 고유 ID"
        text    name             "컬렉션 이름 ('flavor_text')"
        jsonb   cmetadata        "컬렉션 메타데이터"
    }

    langchain_pg_embedding {
        uuid    id           PK  "임베딩 고유 ID"
        uuid    collection_id FK "langchain_pg_collection.uuid 참조"
        vector  embedding        "임베딩 벡터 (1536차원)"
        text    document         "원문 텍스트 (species_id: version content)"
        jsonb   cmetadata        "문서 메타데이터"
    }

    langchain_pg_collection ||--|{ langchain_pg_embedding : "컬렉션 소속 (1:N)"
```

**데이터 흐름:**

```
flavor_text.json
  └─ ingest.py (index_vectorstore)
       └─ OpenAI Embeddings API → vector(1536)
            └─ langchain_pg_embedding.embedding  ← 저장
                 └─ search_flavor_text (MMR 검색) ← 런타임 조회
```

**`langchain_pg_embedding.document` 저장 형식:**

```
"{species_id}: {version_name} {content}"

예시)
"25: 레드 전기를 주머니에 모아두고 필요할 때 방출한다."
```

---

## 3. 채팅 도메인 ERD

```mermaid
erDiagram
    chat_sessions {
        int       id          PK  "세션 고유 ID (SERIAL)"
        text      title           "세션 제목 (첫 질문 앞 60자)"
        text      model           "사용 LLM 모델명"
        text      user_id         "사용자 식별자 (NULL 허용)"
        timestamp created_at      "세션 생성 시각"
    }

    chat_messages {
        int       id          PK  "메시지 고유 ID (SERIAL)"
        int       session_id  FK  "chat_sessions.id 참조"
        text      role            "메시지 역할 (user / assistant)"
        text      content         "메시지 내용"
        text[]    used_tools      "사용된 툴 이름 배열"
        timestamp created_at      "메시지 생성 시각"
    }

    chat_sessions ||--|{ chat_messages : "메시지 포함 (1:N, CASCADE DELETE)"
```

---

## 4. 전체 도메인 관계 개요

```mermaid
flowchart LR
    subgraph PG["PostgreSQL 15"]
        subgraph POKEMON["포켓몬 도메인 (직접 관리)"]
            P["pokemon"]
            PS["pokemon_stats"]
            T["types"]
            PT["pokemon_types"]
            SP["species"]
            FT["flavor_text"]
        end

        subgraph VECTOR["PGVector 도메인 (LangChain 자동 생성)"]
            COL["langchain_pg_collection\nname='flavor_text'"]
            EMB["langchain_pg_embedding\nvector(1536)"]
        end

        subgraph CHAT["채팅 도메인 (직접 관리)"]
            CS["chat_sessions"]
            CM["chat_messages"]
        end
    end

    FT -->|"ingest.py\n원문 텍스트 + 임베딩 생성"| EMB
    COL -->|"1:N"| EMB
    CS -->|"1:N CASCADE"| CM
```

> **포켓몬 도메인**과 **PGVector 도메인**은 물리적으로 같은 PostgreSQL DB에 존재하지만 FK로 직접 연결되지 않습니다.  
> `flavor_text.content`의 텍스트가 `ingest.py`를 통해 `langchain_pg_embedding.document`로 복사·임베딩되는 논리적 연관 관계입니다.

---

## 5. 테이블 상세 명세

### 5.1 pokemon

| 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| `id` | INTEGER | NO | - | PK, 포켓몬 국가도감 번호 |
| `name` | TEXT | NO | - | 한글 이름 |
| `height` | INTEGER | YES | NULL | dm 단위 키 |
| `weight` | INTEGER | YES | NULL | hg 단위 몸무게 |
| `base_exp` | INTEGER | YES | NULL | 기본 획득 경험치 |
| `image_url` | TEXT | YES | NULL | 공식 스프라이트 URL |
| `cry_url` | TEXT | YES | NULL | 울음소리 MP3 URL |
| `is_default` | BOOLEAN | YES | true | 기본 폼 여부 |

### 5.2 pokemon_stats

| 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| `pokemon_id` | INTEGER | NO | - | FK → pokemon.id |
| `hp` | INTEGER | YES | NULL | 체력 스탯 |
| `attack` | INTEGER | YES | NULL | 물리 공격 |
| `defense` | INTEGER | YES | NULL | 물리 방어 |
| `sp_attack` | INTEGER | YES | NULL | 특수 공격 |
| `sp_defense` | INTEGER | YES | NULL | 특수 방어 |
| `speed` | INTEGER | YES | NULL | 스피드 |

### 5.3 types

| 컬럼명 | 데이터 타입 | NULL | 설명 |
|--------|-----------|------|------|
| `id` | INTEGER | NO | PK |
| `name` | TEXT | NO | 타입명 (노말, 불꽃, 물, 풀 등) |

### 5.4 pokemon_types

| 컬럼명 | 데이터 타입 | NULL | 설명 |
|--------|-----------|------|------|
| `pokemon_id` | INTEGER | NO | FK → pokemon.id, 복합 PK |
| `type_id` | INTEGER | NO | FK → types.id, 복합 PK |
| `slot` | INTEGER | NO | 1 = 주 타입, 2 = 서브 타입 |

### 5.5 species

| 컬럼명 | 데이터 타입 | NULL | 설명 |
|--------|-----------|------|------|
| `id` | INTEGER | NO | PK |
| `pokemon_id` | INTEGER | NO | FK → pokemon.id |
| `generation` | INTEGER | YES | 등장 세대 번호 |
| `capture_rate` | INTEGER | YES | 포획률 0~255 |

### 5.6 flavor_text

| 컬럼명 | 데이터 타입 | NULL | 설명 |
|--------|-----------|------|------|
| `id` | INTEGER | NO | PK (SERIAL) |
| `species_id` | INTEGER | NO | FK → species.id |
| `version_name` | TEXT | NO | 게임 버전명 |
| `content` | TEXT | YES | 도감 설명 원문 |
| `embedding` | VECTOR(1536) | YES | OpenAI text-embedding-ada-002 벡터 |

> `embedding` 컬럼은 `pgvector` 확장이 활성화된 경우에만 사용 가능합니다.

### 5.7 langchain_pg_collection *(LangChain 자동 생성)*

| 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| `uuid` | UUID | NO | gen_random_uuid() | PK |
| `name` | TEXT | NO | - | 컬렉션 이름 (`"flavor_text"`) |
| `cmetadata` | JSONB | YES | NULL | 컬렉션 메타데이터 |

### 5.8 langchain_pg_embedding *(LangChain 자동 생성)*

| 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| `id` | UUID | NO | gen_random_uuid() | PK |
| `collection_id` | UUID | YES | NULL | FK → langchain_pg_collection.uuid |
| `embedding` | VECTOR(1536) | YES | NULL | OpenAI 임베딩 벡터 |
| `document` | TEXT | YES | NULL | 원문 텍스트 (`"species_id: version content"`) |
| `cmetadata` | JSONB | YES | NULL | 문서 메타데이터 (필터링용) |

---

## 6. 인덱스 정의

| 테이블 | 인덱스명 | 컬럼 | 타입 | 목적 |
|--------|---------|------|------|------|
| `flavor_text` | `idx_flavor_text_species_id` | `species_id` | B-Tree | 종족 기반 조인 |
| `langchain_pg_embedding` | `idx_lc_embedding_vector` | `embedding` | IVFFlat / HNSW | 벡터 유사도 검색 (MMR) |
| `langchain_pg_embedding` | `idx_lc_embedding_collection` | `collection_id` | B-Tree | 컬렉션 필터링 |
| `chat_messages` | `idx_chat_messages_session_id` | `session_id` | B-Tree | 세션별 메시지 조회 |
| `chat_sessions` | `idx_chat_sessions_user_id` | `user_id` | B-Tree | 사용자별 세션 필터 |
| `pokemon_types` | `idx_pokemon_types_type_id` | `type_id` | B-Tree | 타입별 포켓몬 조회 |

---

## 7. 제약조건 및 참조 무결성

```sql
-- cascade 삭제: 세션 삭제 시 메시지도 자동 삭제
ALTER TABLE chat_messages
  ADD CONSTRAINT fk_messages_session
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
  ON DELETE CASCADE;

-- 복합 PK: 포켓몬당 타입 중복 방지
ALTER TABLE pokemon_types
  ADD CONSTRAINT pk_pokemon_types PRIMARY KEY (pokemon_id, type_id);

-- PGVector 인덱스 (IVFFlat 예시, lists는 데이터 규모에 따라 조정)
CREATE INDEX idx_lc_embedding_vector
  ON langchain_pg_embedding
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```
