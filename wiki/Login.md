# 로그인 (Login) — GitHub OAuth 2.0 트레이너 인증 시스템

GitHub 계정 하나로 포켓몬 월드의 정식 트레이너가 되어 팀 저장·배틀 기록·AI 챗 기능을 이용합니다.

---

## 목차

1. [개요](#1-개요)
2. [기술 스택](#2-기술-스택)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [핵심 기능 상세](#4-핵심-기능-상세)
5. [백엔드 API 명세](#5-백엔드-api-명세)
6. [환경 변수](#6-환경-변수)

---

## 1. 개요

**트레이너 인증 시스템**은 GitHub OAuth 2.0 Authorization Code Flow 기반 소셜 로그인입니다.  
별도 회원가입 없이 GitHub 계정으로 즉시 로그인하며, 인증 완료 시 GitHub 공개 통계(커밋 수·스타 수·팔로워 수)를 자동 수집해 사용자 프로필에 반영합니다.

| 항목 | 내용 |
|---|---|
| 인증 방식 | GitHub OAuth 2.0 Authorization Code Flow |
| 세션 관리 | `st.session_state` + `streamlit-cookies-controller` |
| 주요 파일 | `frontend/pages/login.py`, `frontend/pages/style/login_styles.py` |

---

## 2. 기술 스택

| 구분 | 기술 | 용도 |
|---|---|---|
| Frontend | Streamlit | 페이지 렌더링 및 세션 상태 관리 |
| Frontend | streamlit-cookies-controller | 브라우저 쿠키 기반 세션 영속화 |
| Frontend | HTML/CSS (st.markdown) | Glassmorphism 로그인 카드, 포케볼 SVG 애니메이션 |
| Backend/외부 | GitHub OAuth API | Authorization Code 발급 및 Access Token 교환 |
| Backend/외부 | GitHub REST API v3 | 사용자 프로필·레포지토리·커밋 통계 조회 |
| Backend/외부 | FastAPI `/api/v1/users/` | 사용자 정보 DB 동기화 (Upsert) |
| Backend/외부 | PostgreSQL | 사용자 데이터 영구 저장 |

---

## 3. 시스템 아키텍처

### 3-1. 컴포넌트 구성도

```mermaid
graph TD
    subgraph Browser["브라우저"]
        U[사용자]
        FE["login.py<br/>(Streamlit 프론트엔드)"]
        CK[(쿠키 저장소<br/>user_session)]
    end

    subgraph GitHub["GitHub 서버"]
        GH_AUTH["OAuth Authorization<br/>github.com/login/oauth/authorize"]
        GH_TOKEN["Token 교환<br/>github.com/login/oauth/access_token"]
        GH_API["GitHub REST API v3<br/>api.github.com"]
    end

    subgraph Backend["백엔드 (FastAPI)"]
        BE["POST /api/v1/users/<br/>Upsert 유저 정보"]
        DB[(PostgreSQL)]
    end

    U -- "로그인 버튼 클릭" --> FE
    FE -- "Redirect (client_id, scope)" --> GH_AUTH
    GH_AUTH -- "code (콜백)" --> FE
    FE -- "code + client_secret" --> GH_TOKEN
    GH_TOKEN -- "access_token" --> FE
    FE -- "Authorization: token" --> GH_API
    GH_API -- "user_info + stats" --> FE
    FE -- "POST user payload" --> BE
    BE -- "Upsert" --> DB
    DB -- "db_user" --> BE
    BE -- "UserResponse" --> FE
    FE -- "set cookie" --> CK
    FE -- "st.switch_page(mypage)" --> U
```

### 3-2. 로그인 전체 흐름 시퀀스

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as login.py
    participant GH_O as GitHub OAuth
    participant GH_A as GitHub API
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    User->>FE: "GitHub 계정으로 시작하기" 클릭
    FE->>GH_O: Redirect (client_id, redirect_uri, scope=user:email)
    GH_O-->>User: GitHub 권한 동의 화면
    User->>GH_O: 승인
    GH_O-->>FE: ?code=AUTHORIZATION_CODE (콜백)

    FE->>FE: 포케볼 로딩 화면 표시
    FE->>GH_O: POST /login/oauth/access_token (code + client_secret)
    GH_O-->>FE: access_token

    par GitHub 통계 병렬 수집 (ThreadPoolExecutor)
        FE->>GH_A: GET /user (프로필)
        GH_A-->>FE: user_info (login, name, avatar_url, ...)
        FE->>GH_A: GET /search/commits?q=author:{login}
        GH_A-->>FE: total_commits
        FE->>GH_A: GET /users/{login}/repos
        GH_A-->>FE: total_stars
    end

    FE->>BE: POST /api/v1/users/ (github_id, stats...)
    BE->>DB: Upsert User
    DB-->>BE: db_user (id, ...)
    BE-->>FE: UserResponse

    FE->>FE: st.session_state.user 저장
    FE->>FE: controller.set("user_session", user_info) 쿠키 저장
    FE->>User: st.switch_page("pages/mypage.py")
```

### 3-3. 로그아웃 흐름

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as login.py

    User->>FE: 로그아웃 버튼 클릭
    FE->>User: ?ask_logout=true → 확인 다이얼로그 렌더링
    User->>FE: "예" 클릭 (/login?do_logout=true)
    FE->>FE: controller.remove("user_session") 쿠키 삭제
    FE->>FE: del st.session_state.user
    FE->>FE: st.query_params.clear() + st.rerun()
    FE->>User: 로그인 화면으로 복귀
```

---

## 4. 핵심 기능 상세

### 4-1. GitHub OAuth 2.0 인증

Authorization URL 생성 (`login.py:42-48`):

```python
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": "user:email",     # 최소 권한 원칙 — 공개 이메일만 요청
}
auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
```

- `scope: user:email` — 공개 이메일만 요청하는 최소 권한 원칙 적용
- Authorization Code를 받으면 `query_params["code"]`로 즉시 감지

### 4-2. GitHub 통계 병렬 수집

`ThreadPoolExecutor(max_workers=2)`로 커밋 수·스타 수를 동시에 조회합니다 (`login.py:83-115`).

| 수집 항목 | API 엔드포인트 | 비고 |
|---|---|---|
| `public_repos` | `GET /user` | user_info에서 직접 추출 |
| `total_commits` | `GET /search/commits?q=author:{login}` | Preview Accept 헤더 필요 |
| `total_stars` | `GET /users/{login}/repos?per_page=100` | 레포별 stargazers_count 합산 |
| `followers` | `GET /user` | user_info에서 직접 추출 |

### 4-3. 백엔드 DB 동기화 (Upsert)

인증 완료 후 `POST /api/v1/users/`로 사용자 정보를 전송합니다 (`login.py:117-135`).

- DB 저장 성공 시: `db_user.id`를 `user_info["db_id"]`에 병합
- DB 저장 실패 시: GitHub에서 수집한 통계로 세션 구성 (서비스 장애 무중단)

### 4-4. 세션 이중 영속화

| 저장소 | 키 | 용도 |
|---|---|---|
| `st.session_state` | `user` | Streamlit 재렌더링 간 상태 유지 |
| 브라우저 쿠키 | `user_session` | 탭·새로고침 후에도 로그인 상태 복구 |

### 4-5. UI 화면 상태별 렌더링

| 상태 | 표시 내용 |
|---|---|
| **비로그인** | 포케볼 SVG + "GitHub 계정으로 시작하기" 버튼 + 혜택 배지(팀 저장, 배틀 기록, AI 챗) |
| **OAuth 콜백 처리 중** | 포케볼 스핀 로딩 화면 (`loader-spin` 애니메이션) |
| **로그인 완료** | 프로필 카드 (아바타, 이름, `@login`, 마이페이지 이동 버튼) |
| **로그아웃 확인** | "정말 로그아웃 하시겠습니까?" 2버튼 다이얼로그 |

### 4-6. 디자인 시스템 (Glassmorphism)

`login_styles.py`에 정의된 CSS 변수:

```css
:root {
    --poke-red:    #ff4b4b;
    --poke-yellow: #ffcb05;
    --poke-blue:   #2a75bb;
    --glass-bg:    rgba(8, 4, 22, 0.85);  /* Glassmorphism 카드 배경 */
    --neon-blue:   #00d2ff;
    --neon-purple: #9d50bb;
}
```

| 컴포넌트 | 클래스 | 특징 |
|---|---|---|
| 로그인 카드 | `.login-card` | `backdrop-filter: blur(12px)`, card-reveal 애니메이션 |
| 포케볼 아이콘 | `.card-logo` | SVG 인라인, logo-bounce 상하 부유 효과 |
| GitHub 버튼 | `.github-btn` | hover 시 `translateY(-4px) + scale(1.02)` |
| 아바타 | `.avatar-wrap` | neon-blue→neon-purple 그라디언트 테두리 |
| 로딩 화면 | `.loading-screen` | 전체 화면 블러 오버레이 + 포케볼 스핀 |

---

## 5. 백엔드 API 명세

### `POST /api/v1/users/` — 유저 생성 또는 업데이트

**Request Body**

```json
{
  "github_id": 12345678,
  "login": "octocat",
  "name": "The Octocat",
  "avatar_url": "https://avatars.githubusercontent.com/u/583231",
  "email": "octocat@github.com",
  "public_repos": 42,
  "total_commits": 1234,
  "total_stars": 56
}
```

**Response `200 OK`**

```json
{
  "id": 1,
  "github_id": 12345678,
  "login": "octocat",
  "name": "The Octocat",
  "avatar_url": "...",
  "public_repos": 42,
  "total_commits": 1234,
  "total_stars": 56,
  "followers": 0
}
```

### `GET /api/v1/users/{github_id}` — 유저 조회

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `github_id` | `int` | GitHub 사용자 고유 ID |

- `404 Not Found` — 존재하지 않는 유저

---

## 6. 환경 변수

| 변수명 | 설명 |
|---|---|
| `GITHUB_CLIENT_ID` | GitHub OAuth App의 Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App의 Client Secret |
| `GITHUB_REDIRECT_URI` | OAuth 콜백 URI (기본값: `http://localhost:8501/login`) |
| `BACKEND_URL` | 백엔드 API 주소 (기본값: `http://localhost:8000`) |

GitHub OAuth App 생성:
1. `github.com/settings/developers` → **New OAuth App**
2. Homepage URL: `http://localhost:8501`
3. Authorization callback URL: `http://localhost:8501/login`
4. 생성된 **Client ID**와 **Client Secret**을 `.env`에 입력
