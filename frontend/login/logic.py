import streamlit as st
import os
import time
import textwrap
import base64
from login.styles import get_login_styles, POKEBALL_SVG
from utils.ui import inject_common_ui, controller
from .api import (
    get_github_auth_url, get_access_token, get_user_info,
    fetch_lifetime_stats, sync_user_to_db, CLIENT_ID, CLIENT_SECRET
)

def get_base64_img(file_name):
    # 탐색 우선 순위: 1. 배경폴더, 2. 캐릭터폴더, 3. 기본이미지폴더
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subfolders = ["main_background", "main_character", ""]
    
    for sub in subfolders:
        if sub:
            path = os.path.join(base_dir, "img", sub, file_name)
        else:
            path = os.path.join(base_dir, "img", file_name)
            
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

def show_login_page():
    # 1. 공통 UI 주입 및 쿠키 복구
    inject_common_ui(show_header=False)

    # 2. 배경 및 스타일 적용
    bg_base64 = get_base64_img("login_background.png")
    st.markdown(get_login_styles(bg_base64), unsafe_allow_html=True)

    # 3. 로그아웃 최종 처리
    if st.query_params.get("do_logout") == "true":
        controller.remove("user_session")
        if "user" in st.session_state:
            del st.session_state.user
        st.query_params.clear()
        st.switch_page("app.py") # Updated from st.rerun() or pages/login.py based on user's recent diff

    # 4. OAuth 콜백 처리
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        st.query_params.clear()
        
        loading_placeholder = st.empty()
        loading_placeholder.markdown(f"""
            <div class="loading-screen">
                <div class="loader-ball">{POKEBALL_SVG}</div>
                <div class="loading-text">인증 및 로그인 중...</div>
            </div>
        """, unsafe_allow_html=True)
        
        token = get_access_token(code)
        if token:
            user_info = get_user_info(token)
            if user_info:
                gh_stats = fetch_lifetime_stats(user_info)
                db_user = sync_user_to_db(user_info, gh_stats)
                if db_user:
                    user_info["db_id"] = db_user.get("id")
                    user_info.update({
                        "public_repos": db_user.get("public_repos", 0),
                        "total_commits": db_user.get("total_commits", 0),
                        "total_stars": db_user.get("total_stars", 0),
                        "followers": db_user.get("followers", 0)
                    })
                else:
                    user_info.update({
                        "public_repos": gh_stats.get("public_repos", 0),
                        "total_commits": gh_stats.get("total_commits", 0),
                        "total_stars": gh_stats.get("total_stars", 0),
                        "followers": gh_stats.get("followers", 0),
                    })
                st.session_state.user = user_info
                controller.set("user_session", user_info)
                
                loading_placeholder.empty()
                time.sleep(0.1)
                st.switch_page("app.py") # Updated based on user's recent diff
        else:
            loading_placeholder.empty()
            st.error("인증 토큰을 가져오지 못했습니다.")

    # 5. 화면 렌더링
    if "user" in st.session_state:
        handle_logged_in_view()
    else:
        handle_logged_out_view()

def handle_logged_in_view():
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

def handle_logged_out_view():
    if not CLIENT_ID or not CLIENT_SECRET:
        st.warning("⚠️ .env 파일에 GITHUB_CLIENT_ID와 GITHUB_CLIENT_SECRET을 설정해주세요.")
        
    auth_url = get_github_auth_url()
    login_html = textwrap.dedent(f"""
<div class="login-scene">
<div class="login-card">
{POKEBALL_SVG}
<h1 class="login-title">트레이너 인증</h1>
<p class="login-subtitle">포켓몬 월드의 정식 트레이너가 되어<br>나만의 팀과 기록을 관리하세요.</p>
<a href="{auth_url}" target="_top" class="github-btn">
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
