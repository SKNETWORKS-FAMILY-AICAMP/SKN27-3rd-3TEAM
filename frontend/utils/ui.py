import streamlit as st
import streamlit.components.v1 as components
import json
from streamlit_cookies_controller import CookieController
import textwrap

# 쿠키 컨트롤러 초기화 (페이지 최상단)
controller = CookieController()

def inject_common_ui(spacer=False, show_header=True):
    """
    Injects common UI elements with zero-indentation and forces FULL WIDTH layout.
    """
    
    # 1. 쿠키에서 로그인 정보 복구
    if "user" not in st.session_state:
        saved_user = controller.get("user_session")
        if saved_user:
            try:
                if isinstance(saved_user, str):
                    st.session_state.user = json.loads(saved_user)
                else:
                    st.session_state.user = saved_user
            except:
                pass

    # 2. 헤더 관련 HTML 생성
    nav_html = ""
    header_css = ""
    
    if show_header:
        user = st.session_state.get("user")
        if user:
            avatar_url = user.get("avatar_url", "https://cdn-icons-png.flaticon.com/512/1144/1144760.png")
            user_name = user.get("login", "트레이너")
            nav_right_content = f'<a href="/login" target="_self" class="nav-aux"><img src="{avatar_url}" style="border-radius:50%; border:2px solid #ffcb05; width:32px; height:32px; object-fit:cover; margin-bottom:5px;"><span style="color:#2a75bb; font-weight:800; font-size:12px;">{user_name}</span></a>'
        else:
            nav_right_content = '<a href="/login" target="_self" class="nav-aux"><img src="https://cdn-icons-png.flaticon.com/512/1144/1144760.png" style="width:32px; height:32px; margin-bottom:5px;"><span>로그인</span></a>'

        nav_html = textwrap.dedent(f"""
<nav class="top-nav">
<div class="nav-left">
<a href="/" target="_self">
<img src="https://upload.wikimedia.org/wikipedia/commons/9/98/International_Pok%C3%A9mon_logo.svg" class="nav-brand-img">
</a>
</div>
<div class="nav-center">
<a href="/battle" target="_self" class="nav-item">
<img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png">
<span>배틀</span>
</a>
<a href="/pokedex" target="_self" class="nav-item">
<img src="https://i.namu.wiki/i/FN4gFeempIO4XLhMWDyRSdgwt1cZqjhLoKWd9LWeuCYZDxtms3KI2SYFGu0aums30_gue9mPnRmKkO_K8v1mDQ.webp">
<span>도감</span>
</a>
<a href="/chatbot" target="_self" class="nav-item">
<img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/exp-share.png">
<span>AI 박사</span>
</a>
<a href="/teambuilding" target="_self" class="nav-item">
<img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/132.png">
<span>팀 빌더</span>
</a>
<a href="/mini_game" target="_self" class="nav-item">
<img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png">
<span>미니게임</span>
</a>
</div>
<div class="nav-right">
{nav_right_content}
</div>
</nav>
        """).strip()
        
        if spacer:
            nav_html += '<div style="height:90px; width:100%;"></div>'
    else:
        header_css = ".top-nav { display: none !important; }"

    # 3. Global CSS 주입 (풀 너비 강제 및 기본 여백 제거)
    common_css = textwrap.dedent(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');

/* 핵심: 사이트 전체 풀 너비 강제 */
html, body, [data-testid="stAppViewContainer"], .stApp {{ 
    margin: 0; padding: 0; 
    font-family: 'Inter', sans-serif;
}}

.block-container {{ 
    padding: 0 !important; 
    margin: 0 !important; 
    max-width: 100% !important; 
    width: 100% !important;
}}

/* 툴바 및 기본 헤더 숨김 */
#MainMenu, header, footer, 
[data-testid="stHeader"], 
[data-testid="stToolbar"], 
[data-testid="stSidebar"], 
[data-testid="collapsedControl"] {{ 
    display: none !important; 
}}

.top-nav {{ 
    position: absolute; top: 0; left: 0; width: 100%; 
    height: 90px; background: #ffffff; border-bottom: 2px solid #f0f0f0; 
    display: flex; align-items: stretch; justify-content: space-between; 
    padding: 0; z-index: 1000; box-shadow: 0 4px 15px rgba(0,0,0,0.03); 
}}
{header_css}

.nav-left {{ display: flex; align-items: center; padding: 0 30px; border-right: 1px solid #eee; }}
.nav-brand-img {{ height: 45px; width: auto; }}
.nav-center {{ display: flex; flex: 1; justify-content: center; }}
.nav-item {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 25px; color: #000000 !important; font-weight: 500; text-decoration: none !important; font-size: 13px; transition: all 0.2s ease; border-right: 1px solid #eee; min-width: 110px; }}
.nav-item:first-child {{ border-left: 1px solid #eee; }}
.nav-item img {{ width: 38px; height: 38px; margin-bottom: 8px; object-fit: contain; }}
.nav-item:hover {{ background: #fafafa; color: #3b82f6 !important; }}
.nav-right {{ display: flex; align-items: stretch; }}
.nav-aux {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 25px; color: #000000 !important; font-size: 12px; font-weight: 500; text-decoration: none !important; border-left: 1px solid #eee; min-width: 100px; }}
.nav-aux:hover {{ background: #f9f9f9; }}
</style>
    """).strip()
    
    st.markdown(common_css + nav_html, unsafe_allow_html=True)

    # 4. Mouse Follower JS
    components.html("""
    <script>
        (function() {
            const parentWin = window.parent;
            const parentDoc = parentWin.document;
            if (!parentDoc.querySelector('.cursor-follower')) {
                const style = parentDoc.createElement('style');
                style.innerHTML = ".cursor-follower { position: fixed; width: 30px; height: 30px; background: url('https://pokemonkorea.co.kr/img/_con.ico') no-repeat center/contain; pointer-events: none; z-index: 99999; display: none; top: 0; left: 0; will-change: transform; }";
                parentDoc.head.appendChild(style);
                const follower = parentDoc.createElement('div');
                follower.className = 'cursor-follower';
                parentDoc.body.appendChild(follower);
            }
            const follower = parentDoc.querySelector('.cursor-follower');
            if (parentWin._pokeBallListener) {
                parentDoc.removeEventListener('mousemove', parentWin._pokeBallListener);
            }
            parentWin._pokeBallListener = function(e) {
                if (follower) {
                    follower.style.display = 'block';
                    follower.style.transform = `translate3d(${e.clientX + 10}px, ${e.clientY + 10}px, 0)`;
                }
            };
            parentDoc.addEventListener('mousemove', parentWin._pokeBallListener);
        })();
    </script>
    """, height=0)
