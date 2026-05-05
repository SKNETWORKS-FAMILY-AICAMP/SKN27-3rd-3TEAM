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

    /* Header Navigation */
    .top-nav {
        position: fixed; top: 0; left: 0; right: 0; height: 72px;
        background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(0,0,0,0.05);
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 5%; z-index: 1000;
    }
    .nav-brand {
        font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 900;
        background: linear-gradient(135deg, #FFCB05, #EA580C);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-decoration: none !important; letter-spacing: -0.5px;
    }
    .nav-brand:hover { text-decoration: none !important; }

    .nav-menu { display: flex; gap: 32px; }
    .nav-item { 
        display: flex; align-items: center; gap: 8px; 
        color: #4B5563; font-weight: 700; text-decoration: none !important; 
        font-size: 16px; transition: 0.3s; 
    }
    .nav-item img { width: 24px; height: 24px; transition: transform 0.3s; }
    .nav-item:hover { color: #F59E0B; text-decoration: none !important; }
    .nav-item:hover img { transform: scale(1.2) rotate(-10deg); }
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
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/potion.png"> AI 박사
            </a>
            <a href="/teambuilding" target="_self" class="nav-item">
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png"> 팀 빌더
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
