# Backend Graph 모듈 설명

이 폴더는 백엔드가 Neo4j Graph DB와 대화하기 위한 최소 공통 모듈입니다.

팀 빌딩 기능에서 포켓몬 타입 상성, 약점/저항 관계, 배울 수 있는 기술 타입 등을 조회해야 하므로 PostgreSQL만으로 처리하기보다 Neo4j의 관계 탐색을 함께 사용합니다.

---

## 1. 폴더의 역할

`backend/graph`는 크게 두 가지 책임을 가집니다.

| 파일 | 핵심 역할 |
| --- | --- |
| `neo4j_client.py` | Neo4j에 연결하고 Cypher 쿼리를 실행하는 공통 클라이언트 |
| `queries.py` | 팀 분석/추천/배틀에서 사용할 Cypher 쿼리 문자열 모음 |

즉, 이 폴더는 직접 “추천 점수 계산”을 담당하지 않습니다.

Neo4j에 연결하고, 필요한 그래프 데이터를 가져오는 기반 계층입니다.

---

## 2. `neo4j_client.py`

### 목적

`neo4j_client.py`는 백엔드 코드가 Neo4j에 접근할 때 매번 연결 코드를 새로 작성하지 않도록 만든 공통 연결 파일입니다.

FastAPI 라우터나 서비스에서는 이 파일의 `get_neo4j()`를 통해 Neo4j 클라이언트를 주입받아 사용합니다.

### 주요 구성

| 구성 | 설명 |
| --- | --- |
| `Neo4jClient` | Neo4j 드라이버를 감싼 클래스 |
| `run_query()` | 읽기용 Cypher 실행 메서드 |
| `run_write()` | 쓰기용 Cypher 실행 메서드 |
| `verify_connection()` | Neo4j 연결 확인용 메서드 |
| `create_neo4j_client_from_env()` | `.env` 환경변수를 읽어 클라이언트 생성 |
| `get_neo4j()` | FastAPI Dependency로 사용할 함수 |

### 연결 방식

환경변수는 다음 값을 기준으로 읽습니다.

| 환경변수 | 의미 |
| --- | --- |
| `GRAPH_DB_URI` | Neo4j Bolt 접속 주소 |
| `GRAPH_DB_USER` | Neo4j 사용자명 |
| `GRAPH_DB_PASSWORD` | Neo4j 비밀번호 |
| `NEO4J_AUTH` | `neo4j/password` 형태의 Docker용 인증 문자열 |

현재 기본 URI는 Docker Compose 내부 통신 기준으로 설계되어 있습니다.

```text
bolt://neo4j:7687
```

여기서 `7687`은 Neo4j의 Bolt 프로토콜 포트입니다.

Neo4j Browser는 `7474`를 사용하고, Python 백엔드가 쿼리를 실행할 때는 `7687`을 사용합니다.

### 설계 의도

백엔드에서 Neo4j를 사용할 때 아래처럼 직접 드라이버를 계속 만들면 코드가 중복됩니다.

```python
GraphDatabase.driver(uri, auth=(user, password))
```

그래서 `Neo4jClient`로 감싸서 다음처럼 간단히 사용할 수 있게 만들었습니다.

```python
graph.run_query(query, parameters)
```

이 구조 덕분에 라우터나 서비스는 “연결 방법”을 몰라도 되고, “어떤 쿼리를 실행할지”에만 집중할 수 있습니다.

---

## 3. `queries.py`

### 목적

`queries.py`는 Neo4j에서 실행할 Cypher 쿼리를 한 곳에 모아둔 파일입니다.

서비스 파일 안에 긴 Cypher 문자열이 흩어져 있으면 나중에 유지보수가 어려워집니다.

그래서 자주 쓰는 그래프 조회 쿼리는 이 파일에서 이름을 붙여 관리합니다.

### Cypher란?

Cypher는 Neo4j에서 사용하는 그래프 데이터베이스 쿼리 언어입니다.

SQL이 테이블을 조회한다면, Cypher는 노드와 관계를 조회합니다.

예시는 다음과 같습니다.

```cypher
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
RETURN p.name, t.name
```

이 쿼리는 `Pokemon` 노드가 `HAS_TYPE` 관계로 연결된 `Type` 노드를 조회합니다.

### 현재 쿼리 그룹

| 구분 | 쿼리 | 용도 |
| --- | --- | --- |
| 그래프 상태 확인 | `NODE_COUNT_BY_LABEL` | 라벨별 노드 개수 확인 |
| 그래프 상태 확인 | `RELATIONSHIP_COUNT_BY_TYPE` | 관계 타입별 개수 확인 |
| 팀 분석 | `TEAM_WEAKNESS_SUMMARY` | 선택한 5마리의 타입 약점 평균 계산 |
| 팀 추천 | `DEFENSIVE_CANDIDATES_BY_WEAK_TYPES` | 약점을 저항/무효로 보완할 후보 조회 |
| 팀 추천 | `CANDIDATE_MOVE_TYPES` | 후보가 배울 수 있는 기술 타입 조회 |
| 팀 추천 | `CANDIDATE_TYPES` | 후보 포켓몬 자체 타입 조회 |
| 팀 추천 | `CANDIDATE_USEFUL_MOVES` | 후보의 대표 공격 기술 후보 조회 |
| 팀 분석 | `TEAM_TYPE_DISTRIBUTION` | 선택 팀의 타입 분포 조회 |
| 배틀 기반 | `BATTLE_DEFENSE_MULTIPLIER` | 방어 포켓몬이 특정 공격 타입에 받는 배율 조회 |
| 배틀 기반 | `POKEMON_AVAILABLE_MOVES` | 포켓몬이 배울 수 있는 기술 조회 |
| 배틀 기반 | `POKEMON_AVAILABLE_ABILITIES` | 포켓몬 특성 조회 |

---

## 4. 팀 분석 쿼리 흐름

팀 분석에서 가장 중요한 쿼리는 `TEAM_WEAKNESS_SUMMARY`입니다.

선택된 5마리 포켓몬을 기준으로 각 공격 타입에 얼마나 약한지 평균 배율을 계산합니다.

```text
선택한 Pokemon
  -> AGAINST 관계
  -> 공격 Type
  -> multiplier 평균 계산
```

예를 들어 바위 타입 평균 배율이 `1.8`이라면, 현재 팀은 바위 타입 공격을 평균적으로 1.8배로 받는다는 의미입니다.

이 값은 이후 `team_score_service.py`에서 분석용 점수와 등급으로 변환됩니다.

---

## 5. 팀 추천 쿼리 흐름

추천에서는 먼저 팀의 약점 타입을 찾고, 그 약점을 보완할 후보를 찾습니다.

```text
선택 팀 약점 타입
  -> 후보 Pokemon이 해당 타입을 RESISTANT_TO / VERY_RESISTANT_TO / IMMUNE_TO 하는지 확인
  -> 후보의 기본 능력치, 타입, 기술 타입, 대표 기술 조회
  -> 서비스 계층에서 추천 점수 계산
```

Neo4j는 “후보가 어떤 약점 타입을 막아주는가”를 찾는 데 강합니다.

추천 점수 자체는 `backend/services/team_builder_service.py`에서 계산합니다.

---

## 6. 주의할 점

이 폴더는 그래프 DB 접근 계층입니다.

따라서 아래 작업은 이 폴더보다는 서비스 계층에서 처리하는 것이 좋습니다.

| 작업 | 권장 위치 |
| --- | --- |
| 추천 점수 계산 | `backend/services/team_builder_service.py` |
| 분석 점수 변환 | `backend/services/team_score_service.py` |
| 자연어 해설 생성 | `backend/team_build_rag/answer_generator.py` |
| 프론트 응답 형태 조립 | `backend/routers/team_builder.py` 또는 서비스 |

---

## 7. 확장 방향

앞으로 배틀 기능이 커지면 `queries.py`에 다음 쿼리들이 추가될 수 있습니다.

| 추가 쿼리 | 목적 |
| --- | --- |
| 특정 포켓몬 vs 특정 포켓몬 상성 조회 | 배틀 시 공격/방어 타입 계산 |
| 특정 기술의 실제 유효성 조회 | 기술 타입과 상대 방어 타입 비교 |
| 특성 기반 보정 조회 | 부유, 저수, 타오르는불꽃 같은 특성 반영 |
| 아이템 기반 변화 조회 | 메가스톤, 진화 아이템, 배틀 아이템 반영 |
| 성격 보정 조회 | 공격/특공/스피드 등 능력치 성향 반영 |

현재 구조는 이런 쿼리들이 추가되어도 라우터와 서비스 코드가 크게 흔들리지 않도록 분리해둔 형태입니다.
