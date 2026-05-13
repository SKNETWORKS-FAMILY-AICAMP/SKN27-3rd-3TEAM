import streamlit as st

ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

def show_selector():
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="header-card">
        <h1 style="font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 3rem; color: white; margin: 0;">Pokémon Mini Games</h1>
        <p style="color: #ccc; font-size: 1.1rem; margin: 5px 0 0;">즐기고 싶은 게임을 선택하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    _, col1, col2, _ = st.columns([1, 5, 5, 1])
    
    with col1:
        st.markdown(f"""
        <div class="game-card">
            <img src="{ART_URL}/25.png" style="filter: brightness(0);">
            <div class="game-title">실루엣 퀴즈</div>
            <div class="game-desc">그림자만 보고 어떤 포켓몬인지 맞혀보세요!<br>포켓몬 박사라면 식은 죽 먹기죠?</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Silhouette", key="start_sil"):
            st.switch_page("pages/game_1.py")

    with col2:
        st.markdown(f"""
        <div class="game-card">
            <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png">
            <div class="game-title">포켓몬 랩배틀</div>
            <div class="game-desc">포켓몬들의 찰진 디스전!<br>상성과 설정을 이용한 영혼의 랩 배틀을 감상하세요.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Battle", key="start_battle"):
            st.switch_page("pages/game_2.py")
    
    st.markdown('</div>', unsafe_allow_html=True)
