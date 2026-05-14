# Pokemon World — Wiki 홈

**SKN27-3rd-3TEAM** · SKN AI 캠프 27기 3차 프로젝트

GitHub OAuth 로그인 · AI 챗봇 · 포켓덱스 · 팀 빌더 · 배틀 시뮬레이터 · 미니게임을 갖춘 종합 포켓몬 플랫폼입니다.

---

## 문서 목차

| 문서 | 내용 |
|---|---|
| [Architecture](Architecture) | 프로젝트 파일 구조 · Docker 네트워크 · 서비스 구성 |
| [Database](Database) | PostgreSQL ERD · Neo4j 그래프 스키마 |
| [AI-Pipeline](AI-Pipeline) | LangGraph RAG · 챗봇 에이전트 · 시퀀스 다이어그램 |
| [API-Reference](API-Reference) | 전체 엔드포인트 · 파라미터 · 요청/응답 |
| [Features](Features) | 주요 기능 상세 · 화면 설계 · 페이지 흐름 |
| [Setup](Setup) | 환경 변수 · Docker 실행 · 로컬 개발 |
| [Requirements-and-Testing](Requirements-and-Testing) | 요구사항 명세 · WBS · 테스트 체크리스트 |

---

## 빠른 시작

```bash
cp .env.sample .env
docker compose up --build
```

- Frontend: http://localhost:8501
- Backend: http://localhost:8080
- Neo4j: http://localhost:7474

→ 상세 설치 가이드: [Setup](Setup)
