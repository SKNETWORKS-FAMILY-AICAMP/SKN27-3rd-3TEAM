import streamlit as st
import streamlit.components.v1 as components
import json
from streamlit_cookies_controller import CookieController
import textwrap

# 쿠키 컨트롤러 초기화 (싱글톤 패턴처럼 세션 내 재사용 시도)
if "cookie_controller" not in st.session_state:
    st.session_state.cookie_controller = CookieController()
controller = st.session_state.cookie_controller

POKEBALL_SVG = '<svg class="splash-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="45" fill="white" stroke="#333" stroke-width="2"/><path d="M5 50A45 45 0 0 1 95 50H70A20 20 0 0 0 30 50H5" fill="#E33535" stroke="#333" stroke-width="2"/><circle cx="50" cy="50" r="15" fill="white" stroke="#333" stroke-width="2"/><circle cx="50" cy="50" r="8" fill="white" stroke="#333" stroke-width="1"/></svg>'

def inject_common_ui(spacer=False, show_header=True, hide_sidebar=True):
    # 1. 쿠키에서 로그인 정보 복구
    if "user" not in st.session_state:
        saved_user = controller.get("user_session")
        if saved_user:
            try:
                st.session_state.user = json.loads(saved_user) if isinstance(saved_user, str) else saved_user
            except: pass

    # 2. 헤더 구성
    nav_html = ""
    header_css = ""
    if show_header:
        user = st.session_state.get("user")
        if user:
            avatar_url = user.get("avatar_url", "https://cdn-icons-png.flaticon.com/512/1144/1144760.png")
            nav_right_content = f'<a href="https://chromewebstore.google.com/search/%ED%94%BC%ED%94%BC%EA%B3%A0?hl=ko" target="_blank" class="pipigo-btn"><span>피피고 다운로드</span></a>'
            nav_right_content += f'<a href="/mypage" target="_self" class="nav-aux"><img src="{avatar_url}" style="border-radius:50%; width:28px; height:28px; object-fit:cover;"><span style="color:#2a75bb; font-weight:800; font-size:11px;">{user.get("login", "")}</span></a>'
        else:
            nav_right_content = f'<a href="https://chromewebstore.google.com/search/%ED%94%BC%ED%94%BC%EA%B3%A0?hl=ko" target="_blank" class="pipigo-btn"><span>피피고 다운로드</span></a>'
            nav_right_content += '<a href="/login" target="_self" class="nav-aux"><img src="https://cdn-icons-png.flaticon.com/512/1144/1144760.png" style="width:28px; height:28px;"><span>로그인</span></a>'

        nav_html = textwrap.dedent(f"""
<nav class="top-nav">
<div class="nav-left"><a href="/" target="_self"><img src="https://upload.wikimedia.org/wikipedia/commons/9/98/International_Pok%C3%A9mon_logo.svg" class="nav-brand-img"></a></div>
<div class="nav-center">
<a href="/pokedex" target="_self" class="nav-item"><img src="https://i.namu.wiki/i/FN4gFeempIO4XLhMWDyRSdgwt1cZqjhLoKWd9LWeuCYZDxtms3KI2SYFGu0aums30_gue9mPnRmKkO_K8v1mDQ.webp"><span>도감</span></a>
<a href="/battle" target="_self" class="nav-item"><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png"><span>배틀</span></a>
<a href="/chatbot" target="_self" class="nav-item"><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/exp-share.png"><span>AI 박사</span></a>
<a href="/teambuilding" target="_self" class="nav-item"><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/132.png"><span>팀 빌더</span></a>
<a href="/mini_game" target="_self" class="nav-item"><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png"><span>미니게임</span></a>
</div>
<div class="nav-right">{nav_right_content}</div>
</nav>
        """).strip()
        if spacer: nav_html += '<div style="height:50px; width:100%;"></div>'
    else: header_css = ".top-nav { display: none !important; }"

    splash_html = f'<div id="splash-screen"><div class="splash-content">{POKEBALL_SVG}<div class="splash-text">LOADING</div></div></div>'

    common_css = textwrap.dedent(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&family=Inter:wght@400;700&display=swap');
#splash-screen {{
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: #0a0a0a; z-index: 999999;
    display: flex; justify-content: center; align-items: center; pointer-events: none;
    animation: fadeOut 0.6s forwards cubic-bezier(0.4, 0, 0.2, 1); /* 가속됨: 1.2s -> 0.6s */
}}
.splash-logo {{ width: 80px; height: 80px; animation: pulse 0.8s infinite ease-in-out; }}
.splash-text {{ color: white; font-family: 'Outfit'; font-weight: 900; font-size: 1rem; letter-spacing: 3px; opacity: 0.6; }}
@keyframes fadeOut {{ 0% {{ opacity: 1; visibility: visible; }} 85% {{ opacity: 1; }} 100% {{ opacity: 0; visibility: hidden; }} }}
@keyframes pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} }}

html, body, [data-testid="stAppViewContainer"], .stApp {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
.block-container {{ padding: 0 !important; margin: 0 !important; max-width: 100% !important; width: 100% !important; }}
#MainMenu, header, footer, [data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
{'[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }' if hide_sidebar else ''}
.top-nav {{ position: absolute; top: 0; left: 0; width: 100%; height: 90px; background: #ffffff; border-bottom: 2px solid #f0f0f0; display: flex; align-items: stretch; justify-content: space-between; padding: 0; z-index: 1000; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }}
{header_css}
.nav-left {{ display: flex; align-items: center; padding: 0 30px; border-right: 1px solid #eee; }}
.nav-brand-img {{ height: 40px; }}
.nav-center {{ display: flex; flex: 1; justify-content: center; }}
.nav-item {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 20px; color: #000 !important; text-decoration: none !important; font-size: 12px; border-right: 1px solid #eee; min-width: 100px; }}
.nav-item:first-child {{ border-left: 1px solid #eee; }}
.nav-item img {{ width: 32px; height: 32px; margin-bottom: 5px; }}
.nav-item:hover {{ background: #fafafa; color: #3b82f6 !important; }}
.nav-right {{ display: flex; align-items: stretch; }}
.nav-aux {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 20px; color: #000 !important; text-decoration: none !important; border-left: 1px solid #eee; min-width: 80px; }}

/* Pipigo Download Button (Capsule Style) */
.pipigo-btn {{
    display: flex; align-items: center; justify-content: center;
    border: 2px solid #2a75bb; border-radius: 50px;
    padding: 0 25px; margin: 22px 15px;
    color: #2a75bb !important; font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 13px;
    text-decoration: none !important; transition: all 0.2s ease;
    background: #ffffff; cursor: pointer;
    outline: none !important; -webkit-tap-highlight-color: transparent;
}}
.pipigo-btn:hover {{
    background: #2a75bb; color: #ffffff !important;
    box-shadow: 0 4px 15px rgba(42, 117, 187, 0.25);
    transform: translateY(-1px);
}}
.pipigo-btn:active {{
    transform: scale(0.96);
    background: #1e4f8a; color: #ffffff !important;
    border-radius: 50px !important; /* 원형 유지 강제 */
}}
.pipigo-btn:focus {{
    outline: none !important;
    border-radius: 50px !important;
}}
</style>
    """).strip()
    st.markdown(common_css + splash_html + nav_html, unsafe_allow_html=True)

    # 5. Mouse Follower (선택사항: 너무 무거우면 제거 가능, 여기서는 최적화만 진행)
    components.html("""
    <script>
        (function() {
            const pd = window.parent.document;
            if (!pd.querySelector('.cursor-follower')) {
                const s = pd.createElement('style');
                s.innerHTML = ".cursor-follower { position: fixed; width: 25px; height: 25px; background: url('https://pokemonkorea.co.kr/img/_con.ico') no-repeat center/contain; pointer-events: none; z-index: 99999; display: none; will-change: transform; }";
                pd.head.appendChild(s);
                const f = pd.createElement('div'); f.className = 'cursor-follower'; pd.body.appendChild(f);
            }
            const f = pd.querySelector('.cursor-follower');
            window.parent.onmousemove = (e) => {
                f.style.display = 'block';
                f.style.transform = `translate3d(${e.clientX + 10}px, ${e.clientY + 10}px, 0)`;
            };
        })();
    </script>
    """, height=0)
