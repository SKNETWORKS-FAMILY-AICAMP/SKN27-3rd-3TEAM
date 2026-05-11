import streamlit as st
import requests
import os
import base64
from urllib.parse import urlencode
from dotenv import load_dotenv
import sys
import time
import textwrap

# 스타일 및 에셋 임포트 준비
_frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _frontend_dir not in sys.path:
    sys.path.append(_frontend_dir)
from pages.style.login_styles import get_login_styles, POKEBALL_SVG, FLOATING_SPRITES_HTML
from utils.ui import inject_common_ui, controller

# 환경 변수 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

def get_base64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

def get_secret(key, default=None):
    val = os.getenv(key)
    if val: return val
    try:
        if key in st.secrets: return st.secrets[key]
    except: pass
    return default

CLIENT_ID     = get_secret("GITHUB_CLIENT_ID", "")
CLIENT_SECRET = get_secret("GITHUB_CLIENT_SECRET", "")
REDIRECT_URI  = get_secret("GITHUB_REDIRECT_URI", "http://localhost:8501/login")
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"

def get_github_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "user:email",
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

def get_access_token(code):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            if "error" in res_data:
                st.error(f"GitHub 인증 오류: {res_data.get('error_description')}")
                return None
            return res_data.get("access_token")
    except Exception as e:
        st.error(f"네트워크 오류: {str(e)}")
    return None

def get_user_info(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"사용자 정보 요청 오류: {str(e)}")
    return None

def fetch_lifetime_stats(username):
    stats = {"public_repos": 0, "total_commits": 0, "total_stars": 0}
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Pokemon-Trainer-App"}
    try:
        # 1. 커밋 수
        search_url = f"https://api.github.com/search/commits?q=author:{username}"
        search_headers = headers.copy()
        search_headers["Accept"] = "application/vnd.github.cloak-preview+json"
        s_resp = requests.get(search_url, headers=search_headers, timeout=5)
        if s_resp.status_code == 200:
            stats["total_commits"] = s_resp.json().get("total_count", 0)
        
        # 2. 레포 및 스타 수
        u_resp = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=5)
        if u_resp.status_code == 200:
            u_data = u_resp.json()
            stats["public_repos"] = u_data.get("public_repos", 0)
            
        r_resp = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=5)
        if r_resp.status_code == 200:
            stats["total_stars"] = sum(r.get("stargazers_count", 0) for r in r_resp.json())
    except: pass
    return stats

def sync_user_to_db(user_info, gh_stats):
    url = f"{BACKEND_URL}/api/v1/users/"
    payload = {
        "github_id": user_info.get("id"),
        "login": user_info.get("login"),
        "name": user_info.get("name"),
        "avatar_url": user_info.get("avatar_url"),
        "email": user_info.get("email"),
        "public_repos": gh_stats.get("public_repos", 0),
        "total_commits": gh_stats.get("total_commits", 0),
        "total_stars": gh_stats.get("total_stars", 0)
    }
    try:
        resp = requests.post(url, json=payload, timeout=30) # 타임아웃 30초로 연장
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"백엔드 응답 오류 ({resp.status_code}): {resp.text}")
    except Exception as e:
        st.error(f"DB 동기화 중 네트워크 오류 발생: {str(e)}")
    return None

def show():
    # 1. 공통 UI 주입 및 쿠키 복구
    inject_common_ui(show_header=False)

    # 2. 배경 및 스타일 적용
    bg_path = os.path.join(_frontend_dir, "img", "login.png")
    bg_base64 = get_base64_img(bg_path)
    st.markdown(get_login_styles(bg_base64), unsafe_allow_html=True)

    # 3. 로그아웃 최종 처리
    if st.query_params.get("do_logout") == "true":
        controller.remove("user_session")
        if "user" in st.session_state:
            del st.session_state.user
        st.query_params.clear()
        st.rerun()

    # 4. OAuth 콜백 처리
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        st.query_params.clear()
        
        with st.spinner("트레이너 정보를 인증하는 중..."):
            token = get_access_token(code)
            if token:
                user_info = get_user_info(token)
                if user_info:
                    gh_stats = fetch_lifetime_stats(user_info.get("login"))
                    st.write("DEBUG: Fetched GitHub Stats:", gh_stats) # 디버그용
                    db_user = sync_user_to_db(user_info, gh_stats)
                    if db_user:
                        user_info["db_id"] = db_user.get("id")
                        # DB에서 가져온 최신 스탯을 세션에 병합
                        user_info.update({
                            "public_repos": db_user.get("public_repos"),
                            "total_commits": db_user.get("total_commits"),
                            "total_stars": db_user.get("total_stars")
                        })
                    st.session_state.user = user_info
                    controller.set("user_session", user_info)
                    st.success("인증 및 DB 등록 성공! 마이페이지로 이동합니다...")
                    time.sleep(1)
                    st.switch_page("pages/mypage.py")

    # 5. 화면 렌더링
    if "user" in st.session_state:
        if st.query_params.get("ask_logout") == "true":
            logout_confirm_html = textwrap.dedent(f"""
<div class="login-scene">
<div class="login-card">
{POKEBALL_SVG}
<h2 class="login-title" style="font-size: 24px; margin-bottom: 10px;">로그아웃 하시겠습니까?</h2>
<p class="login-subtitle" style="margin-bottom: 30px;">정말 로그아웃 하시겠습니까?<br>인증 세션이 종료됩니다.</p>
<div style="display: flex; gap: 10px; width: 100%;">
<a href="/login?do_logout=true" target="_self" class="github-btn" style="background: #ff4b4b; flex: 1; text-align: center; justify-content: center;">예</a>
<a href="/login" target="_self" class="github-btn" style="background: #666; flex: 1; text-align: center; justify-content: center;">아니오</a>
</div>
</div>
</div>
            """).strip()
            st.markdown(logout_confirm_html, unsafe_allow_html=True)
        else:
            user = st.session_state.user
            avatar = user.get("avatar_url", "")
            name = user.get("name") or user.get("login", "트레이너")
            login = user.get("login", "")
            
            profile_html = textwrap.dedent(f"""
<div class="login-scene">
<div class="login-card">
<div class="profile-box">
<div class="avatar-wrap">
<img src="{avatar}" class="avatar-img">
</div>
<h2 class="user-name">
{name} <span style="font-size: 16px; opacity: 0.6; font-weight: 500; margin-left: 8px;">@{login}</span>
</h2>
<div style="height: 15px;"></div>
<a href="/mypage" target="_self" class="main-nav-btn">마이페이지로 이동</a>
<div style="height: 10px;"></div>
<a href="/login?ask_logout=true" target="_self" class="github-btn" style="background: linear-gradient(135deg, #ff4b4b 0%, #b91c1c 100%); border-color: rgba(255,255,255,0.2);">로그아웃</a>
</div>
<div style="background:rgba(255,203,5,0.1); border:1px solid rgba(255,203,5,0.2); border-radius:12px; padding:12px; color:#ffcb05; font-size:13px; font-weight:700; margin-bottom:20px; text-align:center;">정식 트레이너 인증 완료</div>
<div class="benefit-row">
<span class="benefit-tag">Lv.99 Master</span>
<span class="benefit-tag">Pokedex 100%</span>
</div>
</div>
</div>
            """).strip()
            st.markdown(profile_html, unsafe_allow_html=True)
    else:
        if not CLIENT_ID or not CLIENT_SECRET:
            st.warning("⚠️ .env 파일에 GITHUB_CLIENT_ID와 GITHUB_CLIENT_SECRET을 설정해주세요.")
            
        auth_url = get_github_auth_url()
        login_html = textwrap.dedent(f"""
<div class="login-scene">
<div class="login-card">
{POKEBALL_SVG}
<h1 class="login-title">트레이너 인증</h1>
<p class="login-subtitle">포켓몬 월드의 정식 트레이너가 되어<br>나만의 팀과 기록을 관리하세요.</p>
<a href="{auth_url}" target="_blank" class="github-btn">
<img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="24" style="filter:invert(1); margin-right:10px;">
GitHub 계정으로 시작하기
</a>
<div class="benefit-row">
<span class="benefit-tag">팀 저장</span>
<span class="benefit-tag">배틀 기록</span>
<span class="benefit-tag">AI 챗</span>
</div>
</div>
</div>
        """).strip()
        st.markdown(login_html, unsafe_allow_html=True)

if __name__ == "__main__":
    show()
