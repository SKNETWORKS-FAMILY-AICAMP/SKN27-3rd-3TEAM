import streamlit as st
import streamlit.components.v1 as components

def inject_common_ui():
    """
    Injects common UI elements (Header, Mouse Follower, Global Styles) 
    into a Streamlit page.
    """
    
    # 1. Global CSS & Header HTML
    common_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        margin: 0; padding: 0;
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFF !important;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu, header, footer { visibility: hidden; }
    [data-testid="stHeader"] { height: 0 !important; }
    [data-testid="block-container"] { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { display: none; }

    /* Header Navigation (상단 고정형 화이트 스타일) */
    .top-nav {
        position: absolute; top: 0; left: 0; right: 0; height: 80px;
        background: #ffffff; /* 불투명 화이트 배경 */
        border-bottom: 1px solid rgba(0,0,0,0.08);
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 5%; z-index: 1000;
    }
    .nav-brand {
        font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 900;
        background: linear-gradient(to right, #FFCB05, #EA580C);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-decoration: none !important; letter-spacing: -1px;
    }
    .nav-brand:hover { text-decoration: none !important; }

    .nav-menu { display: flex; gap: 35px; }
    .nav-item { 
        display: flex; align-items: center; gap: 12px; 
        color: #1f2937; font-weight: 700; text-decoration: none !important; 
        font-size: 17px; transition: 0.2s; 
    }
    .nav-item img { width: 40px; height: 40px; transition: transform 0.3s; object-fit: contain; }
    .nav-item:hover { color: #3b82f6; text-decoration: none !important; }
    .nav-item:hover img { transform: scale(1.1) rotate(-5deg); }
    /* 메타몽 아이콘 슈퍼 스케일 보정 */
    .nav-item[href="/teambuilding"] img { transform: scale(1.6); }
    .nav-item[href="/teambuilding"]:hover img { transform: scale(1.8) rotate(-5deg); }
    </style>

    <nav class="top-nav">
        <a href="/" target="_self" class="nav-brand">POKÉMON WORLD</a>
        <div class="nav-menu">
            <a href="/battle" target="_self" class="nav-item">
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png"> 배틀
            </a>
            <a href="/pokedex" target="_self" class="nav-item">
                <img src="https://i.namu.wiki/i/FN4gFeempIO4XLhMWDyRSdgwt1cZqjhLoKWd9LWeuCYZDxtms3KI2SYFGu0aums30_gue9mPnRmKkO_K8v1mDQ.webp"> 도감
            </a>
            <a href="/chatbot" target="_self" class="nav-item">
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/exp-share.png"> AI 박사
            </a>
            <a href="/teambuilding" target="_self" class="nav-item">
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/132.png"> 팀 빌더
            </a>
        </div>
    </nav>
    """
    st.write(common_html, unsafe_allow_html=True)

    # 2. Mouse Follower JS
    components.html("""
    <script>
        const parentDoc = window.parent.document;
        
        // Only add if not already present
        if (!parentDoc.querySelector('.cursor-follower')) {
            const followerStyle = parentDoc.createElement('style');
            followerStyle.innerHTML = `
                .cursor-follower {
                    position: fixed; width: 30px; height: 30px;
                    background: url('https://pokemonkorea.co.kr/img/_con.ico') no-repeat center/contain;
                    pointer-events: none; z-index: 10000;
                    transform: translate(15px, 15px);
                    display: none;
                    transition: transform 0.05s linear;
                }
            `;
            parentDoc.head.appendChild(followerStyle);

            const follower = parentDoc.createElement('div');
            follower.className = 'cursor-follower';
            parentDoc.body.appendChild(follower);

            parentDoc.addEventListener('mousemove', (e) => {
                follower.style.display = 'block';
                follower.style.left = e.clientX + 'px';
                follower.style.top = e.clientY + 'px';
            });
        }
    </script>
    """, height=0)
