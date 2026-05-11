import streamlit as st
import requests
import os
import base64
from urllib.parse import urlencode
from dotenv import load_dotenv
import sys

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
    resp = requests.post(url, headers=headers, data=data)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None

def get_user_info(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return None

def show():
    # 공통 UI 주입 (쿠키 복구 및 마우스 트래커는 유지하되 헤더는 숨김)
    inject_common_ui(show_header=False)

    # 배경 이미지 로드 및 스타일 주입
    bg_path = os.path.join(_frontend_dir, "img", "login.png")
    bg_base64 = get_base64_img(bg_path)
    st.markdown(get_login_styles(bg_base64), unsafe_allow_html=True)

    # OAuth 콜백 처리
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        st.query_params.clear()
        with st.spinner("트레이너 정보를 불러오는 중..."):
            token = get_access_token(code)
            if token:
                user_info = get_user_info(token)
                if user_info:
                    st.session_state.user = user_info
                    # 쿠키에 세션 저장 (30일 유지)
                    controller.set("user_session", user_info)
                    st.success(f"🎊 {user_info.get('login')}님, 환영합니다!")
                    st.rerun()

    # 화면 렌더링
    if "user" in st.session_state:
        user = st.session_state.user
        avatar = user.get("avatar_url", "")
        name = user.get("name") or user.get("login", "트레이너")
        login = user.get("login", "")
        
        profile_html = f'<div class="login-scene"><div class="login-card"><div class="profile-box"><div class="avatar-wrap"><img src="{avatar}" class="avatar-img"></div><h2 class="user-name">{name}</h2><p class="user-id">@{login}</p><a href="/" target="_self" class="main-nav-btn">🏠 메인 화면으로 이동</a></div><div style="background:rgba(255,203,5,0.1); border:1px solid rgba(255,203,5,0.2); border-radius:12px; padding:12px; color:#ffcb05; font-size:13px; font-weight:700; margin-bottom:20px; text-align:center;">✅ 정식 트레이너 인증 완료</div><div class="benefit-row"><span class="benefit-tag">Lv.99 Master</span><span class="benefit-tag">Pokedex 100%</span></div></div></div>'
        st.markdown(profile_html, unsafe_allow_html=True)
        
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            if st.button("🚪 로그아웃 및 세션 종료", use_container_width=True):
                # 쿠키 삭제
                controller.remove("user_session")
                if "user" in st.session_state:
                    del st.session_state.user
                st.rerun()
    else:
        auth_url = get_github_auth_url()
        login_html = f'<div class="login-scene"><div class="login-card">{POKEBALL_SVG}<h1 class="login-title">트레이너 인증</h1><p class="login-subtitle">포켓몬 월드의 정식 트레이너가 되어<br>나만의 팀과 기록을 관리하세요.</p><a href="{auth_url}" target="_self" class="github-btn"><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="24" style="filter:invert(1); margin-right:10px;">GitHub 계정으로 시작하기</a><div class="benefit-row"><span class="benefit-tag">🛡️ 팀 저장</span><span class="benefit-tag">🔥 배틀 기록</span><span class="benefit-tag">💬 AI 챗</span></div></div></div>'
        st.markdown(login_html, unsafe_allow_html=True)

if __name__ == "__main__":
    show()
