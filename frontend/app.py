import streamlit as st
import streamlit.components.v1 as components

# ── Image Assets ──
ART = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"
GIF = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown"

st.set_page_config(
    page_title="Pokémon World",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global Styles & HTML Layout ──
html_content = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
margin: 0; padding: 0;
font-family: 'Inter', sans-serif;
overflow-x: hidden;
background-color: #F8FAFF !important;
}}
#MainMenu, header, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{ height: 0 !important; }}
[data-testid="block-container"] {{ padding: 0 !important; max-width: 100% !important; }}
[data-testid="stSidebar"] {{ display: none; }}

.top-nav {{
position: fixed; top: 0; left: 0; right: 0; height: 72px;
background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
border-bottom: 1px solid rgba(0,0,0,0.05);
display: flex; align-items: center; justify-content: space-between;
padding: 0 5%; z-index: 1000;
}}
.nav-brand {{
font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 900;
background: linear-gradient(135deg, #FFCB05, #EA580C);
-webkit-background-clip: text; -webkit-text-fill-color: transparent;
text-decoration: none !important; letter-spacing: -0.5px;
}} /* Double braces required for f-string escaping */
.nav-brand:hover {{ text-decoration: none !important; }}
.nav-menu {{ display: flex; gap: 32px; }}
.nav-item {{ display: flex; align-items: center; gap: 8px; color: #4B5563; font-weight: 700; text-decoration: none !important; font-size: 16px; transition: 0.3s; }}
.nav-item img {{ width: 24px; height: 24px; transition: transform 0.3s; }}
.nav-item:hover {{ color: #F59E0B; text-decoration: none !important; }}
.nav-item:hover img {{ transform: scale(1.2) rotate(-10deg); }}

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

.text-box {{ flex: 1; z-index: 2; }}
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
--flip: 1; /* Default no flip */
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

.walk-fast {{ animation-duration: 12s !important; }}
.walk-slow {{ animation-duration: 35s !important; }}

@keyframes walkL {{ from {{ left: 110%; }} to {{ left: -100px; }} }}
@keyframes walkR {{ from {{ left: -100px; }} to {{ left: 110%; }} }}
@keyframes flyUL {{ from {{ left: 110%; top: 80%; }} to {{ left: -100px; top: 10%; }} }}
@keyframes flyUR {{ from {{ left: -100px; top: 80%; }} to {{ left: 110%; top: 20%; }} }}

/* ── BULLETPROOF ANIMATIONS ── */
.reveal-up {{ opacity: 1; transform: translateY(0); }}
.reveal-left {{ opacity: 1; transform: translateX(0); }}
.reveal-right {{ opacity: 1; transform: translateX(0); }}

.js-ready .reveal-up {{ transform: translateY(80px); opacity: 0; transition: all 1s cubic-bezier(0.16, 1, 0.3, 1); }}
.js-ready .reveal-left {{ transform: translateX(-80px); opacity: 0; transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s; }}
.js-ready .reveal-right {{ transform: translateX(80px); opacity: 0; transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s; }}

.js-ready .in-view .reveal-up {{ transform: translateY(0); opacity: 1; }}
.js-ready .in-view .reveal-left {{ transform: translateX(0); opacity: 1; }}
.js-ready .in-view .reveal-right {{ transform: translateX(0); opacity: 1; }}

/* Section Themes */
.sec-hero {{ padding-top: 120px; }}
.sec-hero .section-inner {{ background: radial-gradient(circle at 50% 100%, #1a1a35 0%, #000 100%); color: #fff; }}
.sec-hero .sec-badge {{ background: rgba(255,203,5,0.2); color: #FFCB05; border: 1px solid #FFCB05; }}
.sec-hero .cta-btn {{ background: #FFCB05; color: #000; box-shadow: 0 10px 20px rgba(255,203,5,0.3); }}

.sec-grass .section-inner {{ background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); color: #064e3b; }}
.sec-grass .sec-badge {{ background: #bbf7d0; color: #166534; }}
.sec-grass .cta-btn {{ background: #15803d; color: #fff; box-shadow: 0 10px 20px rgba(21,128,61,0.2); }}

.sec-fire .section-inner {{ background: linear-gradient(135deg, #450a0a 0%, #171717 100%); color: #fecaca; }}
.sec-fire .sec-title {{ color: #fff; }}
.sec-fire .sec-badge {{ background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #ef4444; }}
.sec-fire .cta-btn {{ background: #dc2626; color: #fff; box-shadow: 0 10px 20px rgba(220,38,38,0.3); }}

.sec-psychic .section-inner {{ background: linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%); color: #4a044e; }}
.sec-psychic .sec-badge {{ background: #f5d0fe; color: #86198f; }}
.sec-psychic .cta-btn {{ background: #c026d3; color: #fff; box-shadow: 0 10px 20px rgba(192,38,211,0.2); }}

.sec-ghost .section-inner {{ background: linear-gradient(135deg, #1e1b4b 0%, #000 100%); color: #e0e7ff; }}
.sec-ghost .sec-title {{ color: #fff; }}
.sec-ghost .sec-badge {{ background: rgba(99,102,241,0.2); color: #818cf8; border: 1px solid #818cf8; }}
.sec-ghost .cta-btn {{ background: #4f46e5; color: #fff; box-shadow: 0 10px 20px rgba(79,70,229,0.3); }}

@media (max-width: 1024px) {{
.section-inner {{ flex-direction: column !important; padding: 60px 40px; text-align: center; }}
.text-box {{ margin-bottom: 40px; }}
}}
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

<!-- Hero Section -->
<div class="full-section sec-hero observer-target">
<img src="{GIF}/172.gif" class="decor-sprite walk-right walk-fast" style="bottom: 10%; width: 55px;" title="Click to catch!">
<img src="{GIF}/133.gif" class="decor-sprite walk-left walk-slow" style="top: 20%; width: 65px;" title="Click me!">
<img src="{GIF}/12.gif" class="decor-sprite fly-up-right" style="top: 60%; width: 70px;">
<img src="{GIF}/35.gif" class="decor-sprite walk-left" style="bottom: 5%; width: 45px;">

<div class="section-inner">
<div class="text-box reveal-up">
<div class="sec-badge">Next-Gen Trainer Platform</div>
<h1 class="sec-title">The Ultimate<br>Pokémon Journey</h1>
<p class="sec-desc">최첨단 AI 기술과 데이터 분석을 통해 포켓몬 마스터로 거듭나세요. 배틀, 도감, 팀 빌딩까지 완벽하게 지원합니다.</p>
<a href="#explore" class="cta-btn">모험 시작하기</a>
</div>
<div class="visual-box reveal-right">
<img src="{ART}/25.png" class="main-artwork">
</div>
</div>
</div>

<!-- Section 1: Pokedex -->
<div id="explore" class="full-section sec-grass observer-target">
<img src="{GIF}/10.gif" class="decor-sprite walk-left walk-fast" style="top: 15%; width: 60px;">
<img src="{GIF}/43.gif" class="decor-sprite walk-right" style="bottom: 10%; width: 50px;">
<img src="{GIF}/1.gif" class="decor-sprite walk-left walk-slow" style="top: 40%; width: 70px;">
<img src="{GIF}/46.gif" class="decor-sprite walk-right walk-fast" style="top: 25%; width: 55px;">

<div class="section-inner">
<div class="text-box reveal-left">
<div class="sec-badge">Knowledge</div>
<h2 class="sec-title">전국 포켓몬 도감</h2>
<p class="sec-desc">1세대부터 최신 세대까지 모든 포켓몬의 상세 데이터를 확인하세요. 종족값, 속성, 진화 트리를 한눈에 파악하여 배틀의 기초를 다집니다.</p>
<a href="/pokedex" target="_self" class="cta-btn">도감 열람하기 →</a>
</div>
<div class="visual-box reveal-right">
<img src="{ART}/1.png" class="main-artwork">
</div>
</div>
</div>

<!-- Section 2: Battle -->
<div class="full-section sec-fire reverse observer-target">
<img src="{GIF}/4.gif" class="decor-sprite walk-right walk-fast" style="bottom: 15%; width: 70px;">
<img src="{GIF}/37.gif" class="decor-sprite walk-left walk-slow" style="top: 10%; width: 80px;">
<img src="{GIF}/58.gif" class="decor-sprite walk-right" style="top: 45%; width: 60px;">
<img src="{GIF}/74.gif" class="decor-sprite walk-left" style="bottom: 5%; width: 50px;">

<div class="section-inner">
<div class="text-box reveal-right">
<div class="sec-badge">Simulation</div>
<h2 class="sec-title">실전 배틀 시뮬레이터</h2>
<p class="sec-desc">치열한 배틀 현장을 시뮬레이션 하세요. 상성 분석과 정밀한 데미지 계산기를 통해 상대의 허점을 찌르는 최적의 전략을 수립할 수 있습니다.</p>
<a href="/battle" target="_self" class="cta-btn">배틀 시뮬레이션 →</a>
</div>
<div class="visual-box reveal-left">
<img src="{ART}/6.png" class="main-artwork">
</div>
</div>
</div>

<!-- Section 3: Chatbot -->
<div class="full-section sec-psychic observer-target">
<img src="{GIF}/63.gif" class="decor-sprite walk-left" style="top: 20%; width: 70px;">
<img src="{GIF}/39.gif" class="decor-sprite walk-right walk-fast" style="bottom: 10%; width: 60px;">
<img src="{GIF}/151.gif" class="decor-sprite fly-up-left" style="width: 50px;">
<img src="{GIF}/122.gif" class="decor-sprite walk-right walk-slow" style="top: 50%; width: 65px;">

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
<img src="{GIF}/92.gif" class="decor-sprite walk-right" style="bottom: 25%; width: 80px;">
<img src="{GIF}/41.gif" class="decor-sprite walk-left walk-fast" style="top: 10%; width: 65px;">
<img src="{GIF}/143.gif" class="decor-sprite walk-left walk-slow" style="top: 50%; width: 120px;">
<img src="{GIF}/197.gif" class="decor-sprite walk-right walk-fast" style="bottom: 10%; width: 70px;">

<div class="section-inner">
<div class="text-box reveal-right">
<div class="sec-badge">Strategy</div>
<h2 class="sec-title">최강 팀 빌더</h2>
<p class="sec-desc">나만의 6마리 드림팀을 구축하고 파티의 약점을 진단하세요. 타입 방어 상성을 시각적으로 분석하여 빈틈없는 스쿼드를 완성합니다.</p>
<a href="/teambuilding" target="_self" class="cta-btn">팀 빌딩 시작 →</a>
</div>
<div class="visual-box reveal-left">
<img src="{ART}/94.png" class="main-artwork">
</div>
</div>
</div>

<div style="padding: 60px; text-align: center; background: #F8FAFF; color: #9CA3AF; font-size: 15px; font-weight: 600;">
© 2024 POKÉMON WORLD. Designed for the Next Generation of Trainers.<br>
Powered by Advanced AI & Data Analytics.
</div>"""

clean_html = "\n".join([line.strip() for line in html_content.split("\n")])
st.write(clean_html, unsafe_allow_html=True)

# ── Interactive JS Injection ──
components.html("""
<script>
    const parentDoc = window.parent.document;
    
    // 1. GUARANTEED VISIBILITY LOGIC
    parentDoc.body.classList.add('js-ready');

    // 2. IntersectionObserver for reveal animations
    const scrollContainer = parentDoc.querySelector('.main') || parentDoc.querySelector('[data-testid="stAppViewContainer"]');
    const targets = parentDoc.querySelectorAll('.observer-target');

    if (scrollContainer && targets.length > 0) {
        const ObserverClass = window.parent.IntersectionObserver || window.IntersectionObserver;
        const observerOptions = { root: scrollContainer, rootMargin: '0px', threshold: 0.1 };
        
        const observer = new ObserverClass((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                }
            });
        }, observerOptions);

        targets.forEach(target => observer.observe(target));
        
        scrollContainer.addEventListener('scroll', () => {
            targets.forEach(target => {
                const rect = target.getBoundingClientRect();
                if (rect.top < window.innerHeight - 50) {
                    target.classList.add('in-view');
                }
            });
        }, { passive: true });
        
        setTimeout(() => {
            targets.forEach(target => {
                const rect = target.getBoundingClientRect();
                if (rect.top < window.innerHeight) target.classList.add('in-view');
            });
        }, 300);
    }
    
    // 3. Click-to-Catch Pokemon Interaction
    const sprites = parentDoc.querySelectorAll('.decor-sprite');
    const pokeIds = [1,4,7,25,39,52,54,58,63,65,74,92,94,130,133,143,149,150,151,172,197,212,248,373,448,700];

    sprites.forEach(sprite => {
        sprite.style.pointerEvents = 'auto';
        
        // CSS handles hover scaling and filtering now, no JS mouse events needed!

        sprite.addEventListener('click', function(e) {
            e.preventDefault();
            const randomId = pokeIds[Math.floor(Math.random() * pokeIds.length)];
            
            this.style.opacity = '0';
            this.style.filter = 'brightness(200%)';
            
            setTimeout(() => {
                this.src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${randomId}.gif`;
                this.style.opacity = '';
                this.style.filter = '';
            }, 250);
        });
    });
</script>
""", height=0)
