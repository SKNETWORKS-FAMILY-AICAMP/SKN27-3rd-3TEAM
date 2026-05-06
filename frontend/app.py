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

bg1 = get_base64_img("main_1.png")
bg2 = get_base64_img("main_2.png")
bg3 = get_base64_img("main_3.png")
bg4 = get_base64_img("main_4.png")
bg5 = get_base64_img("main_5.png")

# ── Image Assets ──
ART = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"
GIF = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown"

st.set_page_config(
    page_title="Pokémon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject Common UI (Header, Follower, Global Styles) ──
inject_common_ui()

# ── Page-Specific Styles (Landing Page Sections) ──
landing_css = f"""
<style>
.full-section {{
    padding: 60px 4%;
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
}}

.section-inner {{
    max-width: 1400px; width: 100%;
    border-radius: 48px;
    padding: 80px 100px;
    display: flex; align-items: center; justify-content: space-between; gap: 80px;
    position: relative; z-index: 10;
    box-shadow: 0 30px 60px -15px rgba(0,0,0,0.1);
    overflow: hidden;
}}

.reverse .section-inner {{ flex-direction: row-reverse; }}

.text-box {{ 
    flex: 1; 
    z-index: 2; 
    background: rgba(0, 0, 0, 0.65); 
    padding: 40px; 
    border-radius: 24px; 
    backdrop-filter: blur(12px); 
    border: 1px solid rgba(255, 255, 255, 0.15); 
}}
.visual-box {{ flex: 1.2; display: flex; justify-content: center; position: relative; z-index: 2; }}

.sec-badge {{
    display: inline-block; padding: 8px 20px; border-radius: 100px;
    font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;
    margin-bottom: 24px;
}}
.sec-title {{
    font-family: 'Outfit', sans-serif; font-size: clamp(40px, 5vw, 64px);
    font-weight: 900; line-height: 1.1; margin-bottom: 24px; letter-spacing: -1px;
}}
.sec-desc {{ font-size: 20px; line-height: 1.6; margin-bottom: 40px; }}

.cta-btn {{
    display: inline-flex; align-items: center; padding: 18px 40px; border-radius: 100px;
    font-size: 18px; font-weight: 700; text-decoration: none;
    transition: transform 0.3s, box-shadow 0.3s;
    position: relative; z-index: 60;
}}
.cta-btn:hover {{ transform: translateY(-5px); }}

.main-artwork {{
    width: 100%; max-width: 500px;
    filter: drop-shadow(0 30px 40px rgba(0,0,0,0.3));
    animation: float 4s ease-in-out infinite;
}}
@keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-20px); }} }}

/* ── Interactive Floating Sprites ── */
.decor-sprite {{
    position: absolute; opacity: 0.8; filter: grayscale(20%);
    z-index: 50; 
    transition: filter 0.3s ease, transform 0.3s ease, opacity 0.3s ease;
    --flip: 1;
    --hover-scale: 1;
    transform: scaleX(var(--flip)) scale(var(--hover-scale));
}}

.decor-sprite:hover {{
    --hover-scale: 1.15;
    filter: grayscale(0%) drop-shadow(0 0 10px rgba(255,203,5,0.8));
}}

.walk-left {{ animation: walkL 25s linear infinite; --flip: 1; }}
.walk-right {{ animation: walkR 20s linear infinite; --flip: -1; }}
.fly-up-left {{ animation: flyUL 22s linear infinite; --flip: 1; }}
.fly-up-right {{ animation: flyUR 18s linear infinite; --flip: -1; }}

@keyframes walkL {{ from {{ left: 110%; }} to {{ left: -100px; }} }}
@keyframes walkR {{ from {{ left: -100px; }} to {{ left: 110%; }} }}
@keyframes flyUL {{ from {{ left: 110%; top: 80%; }} to {{ left: -100px; top: 10%; }} }}
@keyframes flyUR {{ from {{ left: -100px; top: 80%; }} to {{ left: 110%; top: 20%; }} }}

/* ── Reveal Animations (Bulletproof System) ── */
.reveal-up {{ opacity: 1; transform: translateY(0); }}
.reveal-left {{ opacity: 1; transform: translateX(0); }}
.reveal-right {{ opacity: 1; transform: translateX(0); }}

/* JS가 작동할 때만 숨김 처리 */
.js-ready .reveal-up {{ transform: translateY(60px); opacity: 0; transition: all 1s cubic-bezier(0.16, 1, 0.3, 1); }}
.js-ready .reveal-left {{ transform: translateX(-60px); opacity: 0; transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s; }}
.js-ready .reveal-right {{ transform: translateX(60px); opacity: 0; transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s; }}

/* 화면에 들어오면 보여줌 */
.js-ready .in-view .reveal-up {{ transform: translateY(0); opacity: 1; }}
.js-ready .in-view .reveal-left {{ transform: translateX(0); opacity: 1; }}
.js-ready .in-view .reveal-right {{ transform: translateX(0); opacity: 1; }}

/* Themes */
.sec-hero {{ padding-top: 120px; }}
.sec-hero .section-inner {{ background: url('{bg1}') center/cover no-repeat; color: #fff; }}
.sec-hero .sec-badge {{ background: rgba(255,203,5,0.2); color: #FFCB05; border: 1px solid #FFCB05; }}
.sec-hero .cta-btn {{ background: #FFCB05; color: #000; box-shadow: 0 10px 20px rgba(255,203,5,0.3); }}

.sec-grass .section-inner {{ background: url('{bg2}') center/cover no-repeat; color: #fff; }}
.sec-grass .sec-title {{ color: #fff; text-shadow: 0 2px 10px rgba(0,0,0,0.7); }}
.sec-grass .sec-desc {{ color: #eee; text-shadow: 0 1px 5px rgba(0,0,0,0.7); font-weight: 500; }}
.sec-grass .sec-badge {{ background: rgba(255,255,255,0.8); color: #166534; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
.sec-grass .cta-btn {{ background: #15803d; color: #fff; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.3); }}

.sec-fire .section-inner {{ background: url('{bg3}') center/cover no-repeat; color: #fff; }}
.sec-fire .sec-title {{ color: #fff; text-shadow: 0 2px 10px rgba(0,0,0,0.7); }}
.sec-fire .sec-desc {{ color: #eee; text-shadow: 0 1px 5px rgba(0,0,0,0.7); font-weight: 500; }}
.sec-fire .sec-badge {{ background: rgba(255,255,255,0.8); color: #ef4444; box-shadow: 0 2px 5px rgba(0,0,0,0.3); border: none; }}
.sec-fire .cta-btn {{ background: #dc2626; color: #fff; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.3); }}

.sec-psychic .section-inner {{ background: url('{bg4}') center/cover no-repeat; color: #fff; }}
.sec-psychic .sec-title {{ color: #fff; text-shadow: 0 2px 10px rgba(0,0,0,0.7); }}
.sec-psychic .sec-desc {{ color: #eee; text-shadow: 0 1px 5px rgba(0,0,0,0.7); font-weight: 500; }}
.sec-psychic .sec-badge {{ background: rgba(255,255,255,0.8); color: #86198f; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
.sec-psychic .cta-btn {{ background: #c026d3; color: #fff; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.3); }}

.sec-ghost .section-inner {{ background: url('{bg5}') center/cover no-repeat; color: #fff; }}
.sec-ghost .sec-title {{ color: #fff; text-shadow: 0 2px 10px rgba(0,0,0,0.7); }}
.sec-ghost .sec-desc {{ color: #eee; text-shadow: 0 1px 5px rgba(0,0,0,0.7); font-weight: 500; }}
.sec-ghost .sec-badge {{ background: rgba(255,255,255,0.8); color: #4f46e5; box-shadow: 0 2px 5px rgba(0,0,0,0.3); border: none; }}
.sec-ghost .cta-btn {{ background: #4f46e5; color: #fff; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.3); }}

@media (max-width: 1024px) {{
    .section-inner {{ flex-direction: column !important; padding: 60px 40px; text-align: center; }}
    .text-box {{ margin-bottom: 40px; }}
}}
</style>
"""

# ── Main Content HTML ──
content_html = f"""
<!-- Hero Section -->
<div class="full-section sec-hero observer-target">
    <div class="section-inner">
        <div class="text-box reveal-up">
            <div class="sec-badge">Next-Gen Trainer Platform</div>
            <h1 class="sec-title">The Ultimate<br>Pokémon Journey</h1>
            <p class="sec-desc">최첨단 AI 기술과 데이터 분석을 통해 포켓몬 마스터로 거듭나세요. 배틀, 도감, 팀 빌딩까지 완벽하게 지원합니다.</p>
            <a href="#explore" class="cta-btn">모험 시작하기</a>
        </div>
        <div class="visual-box reveal-right">
            <!-- <img src="{ART}/25.png" class="main-artwork"> -->
        </div>
    </div>
</div>

<!-- Section 1: Pokedex -->
<div id="explore" class="full-section sec-grass observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Knowledge</div>
            <h2 class="sec-title">전국 포켓몬 도감</h2>
            <p class="sec-desc">1세대부터 최신 세대까지 모든 포켓몬의 상세 데이터를 확인하세요. 종족값, 속성, 진화 트리를 한눈에 파악하여 배틀의 기초를 다집니다.</p>
            <a href="/pokedex" target="_self" class="cta-btn">도감 열람하기 →</a>
        </div>
        <div class="visual-box reveal-right">
            <!-- <img src="{ART}/1.png" class="main-artwork"> -->
        </div>
    </div>
</div>

<!-- Section 2: Battle -->
<div class="full-section sec-fire reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Simulation</div>
            <h2 class="sec-title">실전 배틀 시뮬레이터</h2>
            <p class="sec-desc">치열한 배틀 현장을 시뮬레이션 하세요. 상성 분석과 정밀한 데미지 계산기를 통해 상대의 허점을 찌르는 최적의 전략을 수립할 수 있습니다.</p>
            <a href="/battle" target="_self" class="cta-btn">배틀 시뮬레이션 →</a>
        </div>
        <div class="visual-box reveal-left">
            <!-- <img src="{ART}/6.png" class="main-artwork"> -->
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
            <a href="/chatbot" target="_self" class="cta-btn">박사님과 대화하기 →</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="https://static.wikia.nocookie.net/pokemon/images/a/ab/%EC%98%A4%EB%B0%95%EC%82%AC_%EB%A0%88%EC%B8%A0%EA%B3%A0_%EA%B3%B5%EC%8B%9D_%EC%9D%BC%EB%9F%AC%EC%8A%A4%ED%8A%B8.png/revision/latest/scale-to-width-down/180?cb=20180714100119&path-prefix=ko" class="main-artwork" style="max-width: 250px; image-rendering: pixelated;">
        </div>
    </div>
</div>

<!-- Section 4: Team Builder -->
<div class="full-section sec-ghost reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Strategy</div>
            <h2 class="sec-title">최강 팀 빌더</h2>
            <p class="sec-desc">나만의 6마리 드림팀을 구축하고 파티의 약점을 진단하세요. 타입 방어 상성을 시각적으로 분석하여 빈틈없는 스쿼드를 완성합니다.</p>
            <a href="/teambuilding" target="_self" class="cta-btn">팀 빌딩 시작 →</a>
        </div>
        <div class="visual-box reveal-left">
            <!-- <img src="{ART}/94.png" class="main-artwork"> -->
        </div>
    </div>
</div>

<div style="padding: 60px; text-align: center; background: #F8FAFF; color: #9CA3AF; font-size: 15px; font-weight: 600;">
    © 2024 POKÉMON WORLD. Designed for the Next Generation of Trainers.<br>
    Powered by Advanced AI & Data Analytics.
</div>
"""

# Streamlit Markdown/HTML 파싱 이슈 방지를 위해 인덴트 제거 후 주입
full_html = landing_css + content_html
clean_html = "\n".join([line.strip() for line in full_html.split("\n")])
st.write(clean_html, unsafe_allow_html=True)

# ── Page-Specific JS (Animations & Catch Interaction) ──
components.html("""
<script>
    const parentDoc = window.parent.document;
    
    // 1. Visibility Logic (js-ready class 추가하여 애니메이션 대기 상태로 만듦)
    // 약간의 딜레이를 주어 DOM이 완전히 렌더링된 후 작동하게 함
    setTimeout(() => {
        parentDoc.body.classList.add('js-ready');
    }, 100);

    // 2. IntersectionObserver (화면 진입 시 in-view 클래스 추가)
    const scrollContainer = parentDoc.querySelector('.main') || parentDoc.querySelector('[data-testid="stAppViewContainer"]');
    const targets = parentDoc.querySelectorAll('.observer-target');

    if (scrollContainer && targets.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                }
            });
        }, { 
            root: scrollContainer, 
            threshold: 0.05, // 5%만 보여도 작동하게 낮춤 
            rootMargin: '0px 0px -50px 0px' 
        });
        
        targets.forEach(t => observer.observe(t));
        
        // 스크롤 이벤트 백업 (Observer가 가끔 작동 안할 때를 대비)
        scrollContainer.addEventListener('scroll', () => {
            targets.forEach(t => {
                const rect = t.getBoundingClientRect();
                if (rect.top < window.innerHeight - 100) {
                    t.classList.add('in-view');
                }
            });
        }, { passive: true });
    }
    
    // 3. Click-to-Catch Interaction
    const sprites = parentDoc.querySelectorAll('.decor-sprite');
    const pokeIds = [1,4,7,25,39,52,54,58,63,65,74,92,94,130,133,143,149,150,151,172,197,212,248,373,448,700];

    sprites.forEach(sprite => {
        sprite.style.pointerEvents = 'auto';
        sprite.addEventListener('click', function() {
            const randomId = pokeIds[Math.floor(Math.random() * pokeIds.length)];
            this.style.opacity = '0';
            setTimeout(() => {
                this.src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${randomId}.gif`;
                this.style.opacity = '0.8';
            }, 250);
        });
    });
</script>
""", height=0)
