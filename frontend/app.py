import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from utils.ui import inject_common_ui

def get_base64_img(file_name):
    path = os.path.join(os.path.dirname(__file__), "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

bg1 = get_base64_img("main_8.png")
bg2 = get_base64_img("main_2.png")
bg3 = get_base64_img("main_3.png")
bg4 = get_base64_img("main_4.png")
bg5 = get_base64_img("main_5.png")
obak = get_base64_img("Obak.png")
bg6 = get_base64_img("login.png")
bg7 = get_base64_img("mini_game.png")
bg8 = get_base64_img("main_9.png")
bg9 = get_base64_img("icon.png")
pipigo_img = get_base64_img("main_10.png")
minigame1_img = get_base64_img("silhouette_pikachu.png")
minigame2_img = get_base64_img("rab_battle.png")

# ── Image Assets ──
ART = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"
GIF = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown"

st.set_page_config(
    page_title="포켓몬 비공식 사이트",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject Common UI (Header, Follower, Global Styles) ──
inject_common_ui()

# ── Page-Specific Styles (Premium Pokémon Identity) ──
landing_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

:root {{
    --poke-yellow: #FFCB05;
    --poke-blue: #2A75BB;
    --glass-bg: rgba(15, 15, 15, 0.45); /* 투명도 상향 */
    --glass-border: rgba(255, 255, 255, 0.12);
}}

.stApp {{ background-color: #050505; }}

/* ── Streamlit Container Reset (배경을 꽉 채우기 위함) ── */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    background-color: #000000 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

/* Force Full Width Layout for Landing Page Only */
.main .block-container, [data-testid="stAppViewBlockContainer"] {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
}}

.block-container {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: none !important;
}}
[data-testid="stHeader"], footer, [data-testid="stToolbar"] {{
    display: none !important;
}}



/* ── Global Utilities ── */
.full-section {{
    width: 100%;
    padding: clamp(30px, 5vw, 60px) 4%;
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
    background-attachment: fixed;
    box-sizing: border-box;
    flex-shrink: 0;
}}

/* ── Pokedex Scanline & Grid Effect ── */
.full-section::after {{
    content: ''; position: absolute; inset: 0;
    background: 
        linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%),
        linear-gradient(90deg, rgba(255, 0, 0, 0.02), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.02));
    background-size: 100% 4px, 3px 100%;
    pointer-events: none;
    z-index: 2;
}}

/* ── Section Backgrounds & Overlays ── */
.full-section::before {{
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.7) 100%);
    z-index: 1;
}}

.sec-hero {{ background: url('{bg1}') center/cover no-repeat fixed; }}
.sec-grass {{ background: url('{bg2}') center/cover no-repeat fixed; }}
.sec-fire {{ background: url('{bg3}') center/cover no-repeat fixed; }}
.sec-psychic {{ background: url('{bg4}') center/cover no-repeat fixed; }}
.sec-ghost {{ background: url('{bg5}') center/cover no-repeat fixed; }}

/* ── Holographic Card (콤팩트 디자인) ── */
.section-inner {{
    max-width: 1200px; width: 94%;
    background: var(--glass-bg);
    backdrop-filter: blur(8px) saturate(180%);
    -webkit-backdrop-filter: blur(8px) saturate(180%);
    border: 1px solid var(--glass-border);
    border-radius: clamp(20px, 3vw, 40px);
    padding: clamp(60px, 9vw, 120px) clamp(30px, 5vw, 60px);
    display: flex; align-items: center; justify-content: space-between; gap: clamp(16px, 2.5vw, 30px);
    position: relative; z-index: 10;
    box-shadow: 0 50px 150px rgba(0,0,0,0.9);
}}

.reverse .section-inner {{ flex-direction: row-reverse; }}

/* ── Typography ── */
.text-box {{ flex: 1.2; z-index: 2; }}
.visual-box {{ flex: 1; display: flex; justify-content: center; align-items: center; position: relative; z-index: 2; }}

.sec-badge {{
    display: inline-block; padding: 8px 20px; border-radius: 50px;
    font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;
    margin-bottom: 24px;
    background: rgba(255, 255, 255, 0.15); 
    color: #fff; border: 1px solid rgba(255, 255, 255, 0.4);
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}}

.sec-title {{
    font-family: 'Outfit', sans-serif; font-size: clamp(40px, 4.5vw, 64px);
    font-weight: 900; line-height: 1.1; margin-bottom: 24px; letter-spacing: -1.5px;
    /* 색상은 테마별로 다시 부여 */
}}

.sec-desc {{
    font-family: 'Inter', sans-serif; font-size: clamp(13px, 1.4vw, 19px); line-height: 1.6;
    margin-bottom: clamp(20px, 3vw, 40px); color: #ffffff;
    font-weight: 600;
    max-width: 550px;
    /* 사방으로 진한 검은색 외곽선(Stroke)을 둘러 절대 안 묻히게 함 */
    text-shadow: 
        1px 1px 2px #000, -1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000, 
        0 5px 15px rgba(0,0,0,1);
}}

/* ── CTAs ── */
.cta-btn {{
    display: inline-flex; align-items: center; padding: clamp(12px, 1.4vw, 18px) clamp(24px, 3.5vw, 45px); border-radius: 100px;
    font-family: 'Outfit', sans-serif; font-size: clamp(14px, 1.3vw, 18px); font-weight: 800; text-decoration: none !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative; z-index: 60;
    text-transform: uppercase; letter-spacing: 1.2px;
    border: 2px solid rgba(255,255,255,0.2);
}}

.cta-btn:hover {{ 
    transform: scale(1.05) translateY(-5px); 
    box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    border-color: rgba(255,255,255,0.6);
}}

/* ── Interactive Artwork ── */
.main-artwork {{
    width: clamp(160px, 28vw, 420px);
    max-height: clamp(140px, 25vw, 380px);
    object-fit: contain;
    animation: float 6s ease-in-out infinite;
    transition: all 0.5s ease;
}}

.main-artwork:hover {{ transform: scale(1.02); }}

@keyframes float {{ 
    0%, 100% {{ transform: translateY(0) rotate(0deg); }} 
    50% {{ transform: translateY(-30px) rotate(2deg); }} 
}}

/* ── Decor Sprites ── */
.decor-sprite {{
    position: absolute; opacity: 0.7;
    z-index: 5; transition: all 0.4s ease;
    cursor: pointer;
}}

.decor-sprite:hover {{
    opacity: 1; transform: scale(1.3) rotate(10deg);
    filter: drop-shadow(0 0 25px var(--aura-color, #fff));
}}

/* ── Theme Styling (절대 가독성 버전) ── */
.sec-hero .sec-badge {{ color: #000; border-color: #FFCB05; background: #FFCB05 !important; opacity: 1; }}
.sec-hero .sec-title {{ 
    color: #FFDE00; /* 더 밝고 쨍한 포켓몬 클래식 옐로우 */
    text-shadow: 2px 2px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 8px 20px rgba(0,0,0,0.9), 0 0 40px rgba(255, 222, 0, 0.6); 
}}
.sec-hero .cta-btn {{ background: #FFCB05 !important; color: #000; font-weight: 900; box-shadow: 0 10px 30px rgba(255, 203, 5, 0.4); border-color: #FFCB05; opacity: 1; }}

.sec-hero .main-artwork {{ filter: drop-shadow(0 0 80px rgba(255, 203, 5, 0.5)); width: clamp(220px, 38vw, 560px); max-height: clamp(200px, 36vw, 520px); }}

.sec-grass .sec-badge {{ color: #000; border-color: #4ADE80; background: #4ADE80; }}
.sec-grass .sec-title {{ 
    color: #4ADE80; 
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(74, 222, 128, 0.4); 
}}
.sec-grass .cta-btn {{ background: #22C55E; color: #fff; box-shadow: 0 10px 30px rgba(34, 197, 94, 0.3); }}
.sec-grass .main-artwork {{ filter: drop-shadow(0 0 80px rgba(34, 197, 94, 0.5)); }}

.sec-fire .sec-badge {{ color: #fff; border-color: #E11D48; background: #E11D48; }}
.sec-fire .sec-title {{ 
    color: #FB7185; 
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(251, 113, 133, 0.4); 
}}
.sec-fire .cta-btn {{ background: #E11D48; color: #fff; box-shadow: 0 10px 30px rgba(225, 29, 72, 0.3); }}
.sec-fire .main-artwork {{ filter: drop-shadow(0 0 80px rgba(225, 29, 72, 0.5)); }}

.sec-psychic .sec-badge {{ color: #fff; border-color: #9333EA; background: #9333EA; }}
.sec-psychic .sec-title {{ 
    color: #C084FC; 
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(192, 132, 252, 0.4); 
}}
.sec-psychic .cta-btn {{ background: #9333EA; color: #fff; box-shadow: 0 10px 30px rgba(147, 51, 234, 0.3); }}
.sec-psychic .main-artwork {{ filter: drop-shadow(0 0 80px rgba(147, 51, 234, 0.6)); }}

.sec-ghost .sec-badge {{ color: #fff; border-color: #4F46E5; background: #4F46E5; }}
.sec-ghost .sec-title {{
    color: #818CF8;
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(129, 140, 248, 0.4);
}}
.sec-ghost .cta-btn {{ background: #4F46E5; color: #fff; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.3); }}
.sec-ghost .main-artwork {{ filter: drop-shadow(0 0 80px rgba(79, 70, 229, 0.6)); }}

.sec-water {{ background: url('{bg6}') center/cover no-repeat fixed; }}
.sec-water .sec-badge {{ color: #fff; border-color: #38BDF8; background: #0284C7; }}
.sec-water .sec-title {{
    color: #38BDF8;
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(56, 189, 248, 0.4);
}}
.sec-water .cta-btn {{ background: #0284C7; color: #fff; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.3); }}
.sec-water .main-artwork {{ filter: drop-shadow(0 0 80px rgba(56, 189, 248, 0.6)); }}

.sec-electric {{ background: url('{bg7}') center/cover no-repeat fixed; }}
.sec-electric .sec-badge {{ color: #000; border-color: #FACC15; background: #FACC15; }}
.sec-electric .sec-title {{
    color: #FDE047;
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(253, 224, 71, 0.4);
}}
.sec-electric .cta-btn {{ background: #CA8A04; color: #fff; box-shadow: 0 10px 30px rgba(202, 138, 4, 0.3); }}
.sec-electric .main-artwork {{ filter: drop-shadow(0 0 80px rgba(250, 204, 21, 0.6)); }}

.sec-dragon {{ background: url('{bg8}') center/cover no-repeat fixed; }}
.sec-dragon .sec-badge {{ color: #fff; border-color: #F97316; background: #EA580C; }}
.sec-dragon .sec-title {{
    color: #FB923C;
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(249, 115, 22, 0.4);
}}
.sec-dragon .cta-btn {{ background: #EA580C; color: #fff; box-shadow: 0 10px 30px rgba(234, 88, 12, 0.3); }}
.sec-dragon .main-artwork {{ filter: drop-shadow(0 0 80px rgba(249, 115, 22, 0.6)); }}

.sec-pipigo {{ background: url('{bg9}') center/cover no-repeat fixed; }}
.sec-pipigo .sec-badge {{ color: #000; border-color: #A3E635; background: #A3E635; }}
.sec-pipigo .sec-title {{
    color: #BEF264;
    text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(190, 242, 100, 0.4);
}}
.sec-pipigo .cta-btn {{ background: #A3E635; color: #000; font-weight: 900; box-shadow: 0 10px 30px rgba(163, 230, 53, 0.3); border-color: #A3E635; }}
.sec-pipigo .main-artwork {{ filter: drop-shadow(0 0 80px rgba(163, 230, 53, 0.6)); width: 320px; }}

/* ── Reveal Animations ── */
.js-ready .reveal-up {{ transform: translateY(80px); opacity: 0; transition: all 1.2s cubic-bezier(0.16, 1, 0.3, 1); }}
.js-ready .reveal-left {{ transform: translateX(-80px); opacity: 0; transition: all 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.2s; }}
.js-ready .reveal-right {{ transform: translateX(80px); opacity: 0; transition: all 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.2s; }}

.js-ready .in-view .reveal-up,
.js-ready .in-view .reveal-left,
.js-ready .in-view .reveal-right {{ transform: translate(0); opacity: 1; }}

@media (max-width: 1024px) {{
    .section-inner {{ flex-direction: column !important; padding: 60px 30px; text-align: center; }}
    .text-box {{ margin-bottom: 50px; order: 2; }}
    .visual-box {{ order: 1; }}
    .sec-title {{ font-size: 40px; }}
}}
</style>
"""

# ── Main Content HTML ──
content_html = f"""
<!-- Hero Section -->
<div class="full-section sec-hero observer-target">
    <div class="section-inner">
        <div class="text-box reveal-up">
            <div class="sec-badge">SKN 27기 3조 프로젝트</div>
            <h1 class="sec-title">LLM, 너로 정했다!<br><b>Pokémon</b> AI 어시스턴트</h1>
            <p class="sec-desc">단순한 검색을 넘어, AI가 포켓몬 세계의 모든 것을 분석합니다.<br>전략적 배틀부터 스마트 도감, 전술적인 팀 빌딩, 실시간 AI 챗봇까지<br> 완벽한 트레이너 가이드를 경험하세요.</p>
            <a href="#explore" class="cta-btn">포켓몬 세상으로 이동</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{ART}/10199.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 1: Pokedex -->
<div id="explore" class="full-section sec-grass observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Infinite Knowledge</div>
            <h2 class="sec-title">전국 포켓몬 도감</h2>
            <p class="sec-desc">1세대부터 최신 세대까지 모든 포켓몬의 상세 데이터를 확인하세요. 종족값, 속성, 진화 트리를 한눈에 파악하여 배틀의 기초를 다집니다.</p>
            <a href="/pokedex" target="_self" class="cta-btn">도감 열람하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{ART}/1.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 2: Battle -->
<div class="full-section sec-fire reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Simulation Arena</div>
            <h2 class="sec-title">실전 배틀 시뮬레이터</h2>
            <p class="sec-desc">치열한 배틀 현장을 시뮬레이션 하세요. 상성 분석과 정밀한 데미지 계산기를 통해 상대의 허점을 찌르는 최적의 전략을 수립할 수 있습니다.</p>
            <a href="/battle2" target="_self" class="cta-btn">배틀 시뮬레이션</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{ART}/6.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 3: Chatbot -->
<div class="full-section sec-psychic observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">AI Assistant</div>
            <h2 class="sec-title">AI 포켓몬 박사</h2>
            <p class="sec-desc">어떤 질문이든 해결해 드립니다. 최신 메타와 랭크 배틀 통계를 학습한 AI 전문가에게 실시간으로 팀 조합과 전술을 상담받으세요.</p>
            <a href="/chatbot" target="_self" class="cta-btn">박사님과 대화하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{obak}" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 4: Team Builder -->
<div class="full-section sec-ghost reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Strategy Lab</div>
            <h2 class="sec-title">최강 팀 빌더</h2>
            <p class="sec-desc">나만의 6마리 드림팀을 구축하고 파티의 약점을 진단하세요.<br>타입 상성을 시각적으로 분석하여 빈틈없는 스쿼드를 완성합니다.</p>
            <a href="/teambuilding" target="_self" class="cta-btn">팀 빌딩 시작</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{ART}/94.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 5: Login -->
<div class="full-section sec-water observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Trainer Identity</div>
            <h2 class="sec-title">나만의<br><b>트레이너 카드</b></h2>
            <p class="sec-desc">로그인하면 팀 빌딩 히스토리와 배틀 기록이 저장됩니다.<br>나만의 포켓몬 여정을 기록하고 맞춤형 AI 추천까지 받아보세요.</p>
            <a href="/login" target="_self" class="cta-btn">트레이너 등록하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{ART}/474.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 6: Silhouette Quiz (Mini-game 1) -->
<div class="full-section sec-electric reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Who's That Pokémon?</div>
            <h2 class="sec-title">실루엣으로 맞혀봐!<br><b>이 포켓몬은 누구게?</b></h2>
            <p class="sec-desc">흑백 실루엣만 보고 포켓몬을 맞혀보세요.<br>1세대부터 현재까지, 당신의 포켓몬 지식을 시험할 시간입니다!</p>
            <a href="/game_1" target="_self" class="cta-btn">도전 시작</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{minigame1_img}" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 7: Rap Battle (Mini-game 2) -->
<div class="full-section sec-dragon observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Rap Battle</div>
            <h2 class="sec-title">포켓몬<br><b>랩 배틀</b></h2>
            <p class="sec-desc">포켓몬들의 치열한 언어 대결! AI가 만들어내는 랩 가사로 배틀을 펼쳐보세요.<br>누가 더 강렬한 라임을 뱉을 수 있을까요?</p>
            <a href="/game_2" target="_self" class="cta-btn">배틀 참전하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{minigame2_img}" class="main-artwork">
        </div>
    </div>
</div>

<!-- Section 8: Pipigo Extension -->
<div class="full-section sec-pipigo reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">New Generation Tool</div>
            <h2 class="sec-title">지능형 LLM 어시스턴트<br><b>피피고 (Pipigo)</b></h2>
            <p class="sec-desc">당신의 웹 브라우저 속에 귀여운 포켓몬 파트너가 나타납니다!<br> 지금 바로 경험해 보세요.</p>
            <a href="https://chromewebstore.google.com/search/%ED%94%BC%ED%94%BC%EA%B3%A0?hl=ko" target="_blank" class="cta-btn">웹 스토어에서 보기</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{pipigo_img}" class="main-artwork" style="border-radius: 40px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
        </div>
    </div>
</div>

<div style="padding: 50px 5% 60px; text-align: center; background: #000; color: rgba(255,255,255,0.3); font-size: 13px; font-family: 'Inter', sans-serif; letter-spacing: 1px; border-top: 1px solid rgba(255,255,255,0.03);">
    © 2026 POKÉMON AI ASSISTANT. ALL RIGHTS RESERVED.<br>
<span style="display: inline-block; margin-top: 10px; opacity: 0.6;">새로운 시대를 탐험하는 트레이너를 위한 지능형 가이드 · Powered by Advanced AI</span>
</div>
</div>
"""

# ── Render Page ──

# 1. Inject CSS separately for reliability
st.markdown(f"<style>{landing_css}</style>", unsafe_allow_html=True)

# 2. Inject Content HTML
st.markdown(content_html, unsafe_allow_html=True)

# 3. Inject JS via a separate markdown block to avoid string issues
# f-string 안의 중괄호를 이스케이프({{, }})하여 파이썬 오류 방지
st.markdown(f"""
<script>
    const parentDoc = window.parent.document;

    // 0. Scroll Snap + Dynamic Height Setup
    const snapContainer = parentDoc.querySelector('.main') || parentDoc.querySelector('[data-testid="stAppViewContainer"]');
    if (snapContainer) {{
        snapContainer.style.scrollSnapType = 'y mandatory';
        snapContainer.style.overflowY = 'scroll';
    }}

    function applySnapHeights() {{
        const vh = window.parent.innerHeight;
        parentDoc.querySelectorAll('.full-section').forEach(el => {{
            el.style.height = vh + 'px';
            el.style.scrollSnapAlign = 'start';
            el.style.scrollSnapStop = 'always';
        }});
    }}

    applySnapHeights();
    window.parent.addEventListener('resize', applySnapHeights);

    // 1. Visibility Logic
    setTimeout(() => {{
        parentDoc.body.classList.add('js-ready');
    }}, 100);

    // 2. IntersectionObserver
    const scrollContainer = parentDoc.querySelector('.main') || parentDoc.querySelector('[data-testid="stAppViewContainer"]');
    const targets = parentDoc.querySelectorAll('.observer-target');

    if (scrollContainer && targets.length > 0) {{
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('in-view');
                }}
            }});
        }}, {{ 
            root: scrollContainer, 
            threshold: 0.05,
            rootMargin: '0px 0px -50px 0px' 
        }});
        
        targets.forEach(t => observer.observe(t));
        
        scrollContainer.addEventListener('scroll', () => {{
            targets.forEach(t => {{
                const rect = t.getBoundingClientRect();
                if (rect.top < window.innerHeight - 100) {{
                    t.classList.add('in-view');
                }}
            }});
        }}, {{ passive: true }});
    }}
    
    // 3. Click-to-Catch Interaction
    const sprites = parentDoc.querySelectorAll('.decor-sprite');
    const pokeIds = [1,4,7,25,39,52,54,58,63,65,74,92,94,130,133,143,149,150,151,172,197,212,248,373,448,700];

    sprites.forEach(sprite => {{
        sprite.style.pointerEvents = 'auto';
        sprite.addEventListener('click', function() {{
            const randomId = pokeIds[Math.floor(Math.random() * pokeIds.length)];
            this.style.opacity = '0';
            setTimeout(() => {{
                this.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/' + randomId + '.gif';
                this.style.opacity = '0.8';
            }}, 250);
        }});
    }});
</script>
""", unsafe_allow_html=True)
