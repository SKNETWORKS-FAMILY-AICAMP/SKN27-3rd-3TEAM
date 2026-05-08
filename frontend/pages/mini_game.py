import streamlit as st
import requests
import random
import os
import sys
import base64

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

# ── Backend Configuration ─────────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_V1_STR = "/api/v1/pokemon"

# ── Image Assets ──────────────────────────────────────────────
ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"
GIF_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown"

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 미니 게임",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_base64_img(file_name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

bg_img = get_base64_img("mini_game.png")

# ── Inject Common UI ──────────────────────────────────────────
inject_common_ui(spacer=False)

# ── Session State Initialization ──────────────────────────────
if "game_mode" not in st.session_state:
    st.session_state.game_mode = None  # None, "silhouette", "memory"

# Silhouette Game State (Moved to game_1.py)

# Memory Game State
if "mem_cards" not in st.session_state:
    st.session_state.mem_cards = []
if "mem_flipped" not in st.session_state:
    st.session_state.mem_flipped = []
if "mem_matched" not in st.session_state:
    st.session_state.mem_matched = set()
if "mem_moves" not in st.session_state:
    st.session_state.mem_moves = 0

# ── Styles ───────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

:root {{
    --glass-bg: rgba(20, 20, 20, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
    --poke-red: #E33535;
}}

/* 배경 이미지를 모든 주요 컨테이너에 강제 적용 */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
    background: url('{bg_img}') center/cover no-repeat fixed !important;
    background-color: #000000 !important;
}}

/* 내부 컨테이너를 투명하게 설정하여 배경이 보이도록 함 */
[data-testid="stAppViewBlockContainer"], .main {{
    background-color: transparent !important;
}}

.game-container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 10px 20px;
    text-align: center;
}}

/* ── Selection Cards ── */
.selection-row {{
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 20px;
    flex-wrap: wrap;
}}

.game-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 40px;
    width: 95%;
    margin: 0 auto;
    padding: 40px 20px 65px;
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    cursor: pointer;
    position: relative;
    overflow: hidden;
    box-shadow: 0 30px 100px rgba(0,0,0,0.6);
}}

.game-card:hover {{
    transform: translateY(-15px) scale(1.02);
    border-color: var(--poke-red);
    box-shadow: 0 30px 80px rgba(227, 53, 53, 0.3);
}}

.game-card img {{
    width: 250px;
    height: 250px;
    object-fit: contain;
    display: block;
    margin: 0 auto 15px;
    filter: drop-shadow(0 15px 35px rgba(0,0,0,0.4));
}}

.game-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 2.0rem;
    font-weight: 900;
    color: #fff;
    margin-bottom: 5px;
    letter-spacing: 1px;
    text-shadow: 0 2px 10px rgba(255, 255, 255, 0.2);
}}

.game-desc {{
    font-family: 'Inter', sans-serif;
    color: #ccc;
    font-size: 1.0rem;
    line-height: 1.5;
    font-weight: 400;
    letter-spacing: -0.2px;
}}

/* ── Silhouette Game Styles ── */
.silhouette-img {{
    width: 400px;
    height: 400px;
    object-fit: contain;
    filter: brightness(0);
    transition: filter 1s ease;
}}
.silhouette-img.revealed {{
    filter: brightness(1) drop-shadow(0 0 30px rgba(255,255,255,0.5));
}}

/* ── Memory Game Styles ── */
.memory-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    max-width: 600px;
    margin: 0 auto;
}}

.mem-card {{
    aspect-ratio: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 2rem;
}}

.mem-card.flipped {{
    background: white;
    border-color: #eee;
    transform: rotateY(180deg);
}}

.mem-card img {{
    width: 80%;
    height: 80%;
    object-fit: contain;
}}

/* ── Common Game UI ── */
.back-btn {{
    position: fixed;
    top: 100px;
    left: 40px;
    z-index: 100;
}}

.glass-panel {{
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 30px;
    margin-top: 20px;
}}

/* ── Header Card ── */
.header-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(15px);
    border: 1px solid var(--glass-border);
    border-radius: 25px;
    padding: 20px 60px;
    display: inline-block;
    margin-bottom: 45px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.4);
}}

/* ── Overlay Button to make cards clickable ── */
/* 컬럼 내부의 모든 요소를 감싸는 컨테이너를 상대 좌표로 설정 */
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div {{
    position: relative !important;
    height: 100%;
}}

/* 버튼이 들어있는 컨테이너를 절대 좌표로 설정하여 카드를 덮음 */
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] .element-container:has(button) {{
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: 1000 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

/* 실제 버튼을 투명하게 만들고 전체 영역을 차지하게 함 */
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] button {{
    width: 100% !important;
    height: 100% !important;
    min-height: 350px !important;
    opacity: 0 !important;
    border: none !important;
    cursor: pointer !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}}

/* Optional: Pulse effect for a "Click to start" feel */
.game-card::after {{
    content: 'CLICK TO START';
    position: absolute;
    bottom: 25px;
    left: 50%;
    transform: translateX(-50%);
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 0.8rem;
    color: var(--poke-red);
    opacity: 0;
    transition: opacity 0.3s;
    letter-spacing: 2px;
}}
.game-card:hover::after {{
    opacity: 1;
}}

</style>
""", unsafe_allow_html=True)

# ── Helper Functions ──────────────────────────────────────────

def set_game_mode(mode):
    st.session_state.game_mode = mode
    if mode == "memory":
        reset_memory()

# reset_silhouette removed (Moved to game_1.py)

def reset_memory():
    # Pick 8 random unique pokemon IDs
    ids = random.sample(range(1, 493), 8) # Up to Gen 4 for classic feel
    cards = []
    for pid in ids:
        cards.append({{"id": pid, "img": f"{{GIF_URL}}/{{pid}}.gif"}})
        cards.append({{"id": pid, "img": f"{{GIF_URL}}/{{pid}}.gif"}})
    random.shuffle(cards)
    st.session_state.mem_cards = cards
    st.session_state.mem_flipped = []
    st.session_state.mem_matched = set()
    st.session_state.mem_moves = 0

# ── Game Views ────────────────────────────────────────────────

def show_selector():
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="header-card">
        <h1 style="font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 3rem; color: white; margin: 0; letter-spacing: 1px; text-shadow: 0 2px 10px rgba(227, 53, 53, 0.6);">Pokémon Mini Games</h1>
        <p style="color: #ccc; font-size: 1.1rem; margin: 5px 0 0; font-family: 'Inter', sans-serif; font-weight: 500; letter-spacing: 0.5px; text-shadow: 0 1px 4px rgba(255, 255, 255, 0.2);">즐기고 싶은 게임을 선택하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # [1, 5, 5, 1] 비율로 사이드 여백을 주어 중앙 정렬 강화
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
            <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png">
            <div class="game-title">기억력 게임</div>
            <div class="game-desc">뒤집힌 카드들 속에서 짝을 찾으세요.<br>당신의 기억력은 어느 정도인가요?</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Memory", key="start_mem"):
            set_game_mode("memory")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_silhouette_game():
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 메뉴로 돌아가기", key="back_to_menu"):
        st.session_state.game_mode = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    target = st.session_state.sil_target
    if not target:
        reset_silhouette()
        st.rerun()

    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    
    # 게임 보드 (배경 간섭 차단을 위한 대형 유리 패널)
    _, main_col, _ = st.columns([0.1, 3, 0.1])
    with main_col:
        st.markdown('<div class="glass-panel" style="padding: 40px; margin-top: 20px; box-shadow: 0 40px 100px rgba(0,0,0,0.5);">', unsafe_allow_html=True)
        
        # 상단 타이틀 영역
        st.markdown(f"""
        <div style="display: flex; justify-content: center; width: 100%;">
            <div class="header-card" style="margin-bottom: 30px; background: rgba(0,0,0,0.3);">
                <h1 style="font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2.5rem; color: white; margin: 0; text-shadow: 0 2px 10px rgba(227, 53, 53, 0.6);">Who's That Pokémon?</h1>
                <p style="color: #ccc; font-size: 1rem; margin: 5px 0 0;">그림자의 주인공을 맞혀보세요!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 포켓몬 이미지 디스플레이
        img_class = "silhouette-img" + (" revealed" if st.session_state.sil_revealed else "")
        img_url = f"{ART_URL}/{target['id']}.png"
        st.markdown(f"""
        <div style="display: flex; justify-content: center; margin: 10px 0 30px;">
            <div style="background: rgba(255,255,255,0.05); border-radius: 50%; padding: 30px; backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.1);">
                <img src="{img_url}" class="{img_class}" style="width: 260px; height: 260px; object-fit: contain;">
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.sil_revealed:
            # 정답 공개 상태
            st.markdown(f"""
            <div style="display: flex; justify-content: center; width: 100%;">
                <div class="header-card" style="background: rgba(227, 53, 53, 0.2); border-color: rgba(227, 53, 53, 0.4); margin-bottom: 20px;">
                    <h2 style="color: #FFCB05; font-family: 'Outfit'; font-weight: 900; font-size: 2.2rem; margin: 0;">정답은 {target['name']}!</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            _, bcol, _ = st.columns([1, 2, 1])
            with bcol:
                if st.button("다음 문제 풀기 ✨", key="next_sil", use_container_width=True):
                    reset_silhouette()
                    st.rerun()
        else:
            # 입력 영역 (패널 내부 중앙 정렬)
            _, icol, _ = st.columns([0.5, 2, 0.5])
            with icol:
                col_inp, col_btn = st.columns([3, 1])
                with col_inp:
                    guess = st.text_input("포켓몬 이름 입력", placeholder="이름을 입력하세요...", key="guess_input", label_visibility="collapsed")
                with col_btn:
                    check = st.button("확인", key="check_btn", use_container_width=True)
            
            if (guess and guess.strip() == target["name"]) or (locals().get('check')):
                if guess.strip() == target["name"]:
                    st.session_state.sil_revealed = True
                    st.balloons()
                    st.rerun()
                elif (locals().get('check')):
                    st.error("틀렸습니다! 다시 생각해보세요.")

            # 힌트 및 도구 영역
            st.write("---")
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                if st.button("💡 힌트", key="hint_btn", use_container_width=True):
                    st.session_state.sil_hint_count += 1
                    st.rerun()
            with h_col2:
                if st.button("🤷 포기", key="give_up_btn", use_container_width=True):
                    st.session_state.sil_revealed = True
                    st.rerun()
            with h_col3:
                if st.button("🔄 다른 문제", key="skip_btn", use_container_width=True):
                    reset_silhouette()
                    st.rerun()

            # 힌트 표시
            if st.session_state.sil_hint_count >= 1:
                types = ", ".join([t["type_"]["name"] for t in target.get("types", [])])
                st.info(f"🧬 **타입 힌트:** {types}")
            if st.session_state.sil_hint_count >= 2:
                st.info(f"🔢 **도감 번호:** No.{target['id']}")
            if st.session_state.sil_hint_count >= 3:
                first_char = target["name"][0]
                st.info(f"🔤 **첫 글자 힌트:** '{first_char}' (으)로 시작합니다!")
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_memory_game():
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 메뉴로 돌아가기", key="back_to_menu_mem"):
        st.session_state.game_mode = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    st.markdown('<h2 style="color: white; font-family: \'Outfit\'; font-weight: 900;">포켓몬 짝 맞추기</h2>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #ccc;">시도 횟수: {{st.session_state.mem_moves}} | 맞춘 개수: {{len(st.session_state.mem_matched)}}/8</p>', unsafe_allow_html=True)

    # Grid logic
    cols = st.columns(4)
    for i, card in enumerate(st.session_state.mem_cards):
        with cols[i % 4]:
            is_flipped = i in st.session_state.mem_flipped or i in st.session_state.mem_matched
            if is_flipped:
                st.markdown(f'<div class="mem-card flipped"><img src="{{card["img"]}}"></div>', unsafe_allow_html=True)
            else:
                if st.button("?", key=f"card_{i}", use_container_width=True):
                    if len(st.session_state.mem_flipped) < 2 and i not in st.session_state.mem_flipped:
                        st.session_state.mem_flipped.append(i)
                        
                        # Check match if 2 cards are flipped
                        if len(st.session_state.mem_flipped) == 2:
                            st.session_state.mem_moves += 1
                            idx1, idx2 = st.session_state.mem_flipped
                            if st.session_state.mem_cards[idx1]["id"] == st.session_state.mem_cards[idx2]["id"]:
                                st.session_state.mem_matched.add(idx1)
                                st.session_state.mem_matched.add(idx2)
                                st.session_state.mem_flipped = []
                                st.rerun()
                        st.rerun()

    if len(st.session_state.mem_flipped) == 2:
        if st.button("다음 시도 (카드가 안 맞음)", key="clear_flipped", use_container_width=True):
            st.session_state.mem_flipped = []
            st.rerun()

    if len(st.session_state.mem_matched) == 16:
        st.success(f"축하합니다! {{st.session_state.mem_moves}}번 만에 모두 맞추셨습니다!")
        if st.button("다시 하기", key="reset_mem_btn", use_container_width=True):
            reset_memory()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── Main Loop ────────────────────────────────────────────────

def main():
    if st.session_state.game_mode == "silhouette":
        show_silhouette_game()
    elif st.session_state.game_mode == "memory":
        show_memory_game()
    else:
        show_selector()

if __name__ == "__main__":
    main()
