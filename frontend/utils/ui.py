import streamlit as st
import streamlit.components.v1 as components

def inject_common_ui(spacer=False):
    """
    Injects common UI elements (Header, Mouse Follower, Global Styles) 
    into a Streamlit page.
    """
    
    # 1. Global CSS & Header HTML
    common_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], .stApp {
        margin: 0; padding: 0;
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFF !important;
        overflow-x: hidden;
    }
    
    /* 완벽한 최상단 밀착을 위해 기본 상단 여백 완전 제거 */
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Hide Streamlit default elements completely (사이드바, 툴바 등 완벽 제거) */
    #MainMenu, header, footer, 
    [data-testid="stHeader"], 
    [data-testid="stToolbar"], 
    [data-testid="stSidebar"], 
    [data-testid="collapsedControl"] { 
        display: none !important; 
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Header Navigation (Official Grid Style) */
    .top-nav {
        position: absolute; top: 0; 
        left: 50%; transform: translateX(-50%); width: 100vw; 
        height: 90px;
        background: #ffffff;
        border-bottom: 2px solid #f0f0f0;
        display: flex; align-items: stretch; justify-content: space-between;
        padding: 0; z-index: 1000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    .nav-left { 
        display: flex; align-items: center; padding: 0 30px; 
        border-right: 1px solid #eee;
    }
    .nav-brand-img { height: 45px; width: auto; transition: transform 0.3s; }
    .nav-brand-img:hover { transform: scale(1.05); }

    .nav-center { 
        display: flex; flex: 1; justify-content: center; 
    }
    .nav-item { 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        padding: 0 25px; color: #000000 !important; font-weight: 500; text-decoration: none !important; 
        font-size: 13px; transition: all 0.2s ease; 
        border-right: 1px solid #eee;
        min-width: 110px;
    }
    .nav-item:first-child { border-left: 1px solid #eee; }
    .nav-item img { width: 38px; height: 38px; margin-bottom: 8px; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); object-fit: contain; }
    
    /* 메타몽 특수 스케일 (공식 아트워크 기반) */
    .nav-item[href="/teambuilding"] img { transform: scale(1.3); margin-bottom: 10px; }
    
    .nav-item:hover { background: #fafafa; color: #3b82f6 !important; }
    .nav-item:hover img { transform: translateY(-5px) scale(1.1); }
    .nav-item[href="/teambuilding"]:hover img { transform: scale(1.4) translateY(-5px); }

    .nav-right { 
        display: flex; align-items: stretch; 
    }
    .nav-aux {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 0 25px; color: #000000 !important; font-size: 12px; font-weight: 500;
        text-decoration: none !important; border-left: 1px solid #eee;
        transition: 0.2s;
    }
    .nav-aux:hover { background: #f9f9f9; color: #000; }
    .nav-aux img { width: 32px; height: 32px; margin-bottom: 6px; }
    </style>

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
            <a href="/login" target="_self" class="nav-aux">
                <img src="https://cdn-icons-png.flaticon.com/512/1144/1144760.png">
                <span>로그인</span>
            </a>
        </div>
    </nav>
    """
    
    if spacer:
        common_html += '<div style="height: 50px; width: 100%;"></div>'
        
    st.write(common_html, unsafe_allow_html=True)

    # 2. Mouse Follower JS (최적화 및 프리징 방지)
    components.html("""
    <script>
        (function() {
            const parentWin = window.parent;
            const parentDoc = parentWin.document;
            
            // 1. 요소 및 스타일 생성 (최초 1회만)
            if (!parentDoc.querySelector('.cursor-follower')) {
                const style = parentDoc.createElement('style');
                style.innerHTML = `
                    .cursor-follower {
                        position: fixed;
                        width: 30px;
                        height: 30px;
                        background: url('https://pokemonkorea.co.kr/img/_con.ico') no-repeat center/contain;
                        pointer-events: none;
                        z-index: 99999;
                        display: none;
                        /* transform을 사용하여 성능 최적화 */
                        top: 0;
                        left: 0;
                        will-change: transform;
                    }
                `;
                parentDoc.head.appendChild(style);

                const follower = parentDoc.createElement('div');
                follower.className = 'cursor-follower';
                parentDoc.body.appendChild(follower);
            }

            const follower = parentDoc.querySelector('.cursor-follower');

            // 2. 이벤트 리스너 리프레시 (페이지 전환 시 프리징 방지)
            // 이전 리스너가 있다면 제거하여 중복 등록 및 메모리 누수 방지
            if (parentWin._pokeBallListener) {
                parentDoc.removeEventListener('mousemove', parentWin._pokeBallListener);
            }

            // 새 리스너 정의
            parentWin._pokeBallListener = function(e) {
                if (follower) {
                    follower.style.display = 'block';
                    // transform을 사용하여 렌더링 부하 감소
                    follower.style.transform = `translate3d(${e.clientX + 10}px, ${e.clientY + 10}px, 0)`;
                }
            };

            // 부모 문서에 새 리스너 등록
            parentDoc.addEventListener('mousemove', parentWin._pokeBallListener);
        })();
    </script>
    """, height=0)
