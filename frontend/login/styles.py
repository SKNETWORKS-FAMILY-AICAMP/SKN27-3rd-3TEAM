def get_login_styles(bg_img=""):
    bg_style = f"background: url('{bg_img}') center/cover no-repeat !important;" if bg_img else "background: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #000 100%);"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Noto+Sans+KR:wght@300;400;700;900&display=swap');

:root {{
    --poke-red: #ff4b4b;
    --poke-yellow: #ffcb05;
    --poke-blue: #2a75bb;
    --glass-bg: rgba(8, 4, 22, 0.85);
    --neon-blue: #00d2ff;
    --neon-purple: #9d50bb;
}}

/* ── 전체 화면 레이아웃 최적화 ── */
[data-testid="stAppViewContainer"] {{
    background: #000 !important;
}}
[data-testid="stHeader"], [data-testid="stToolbar"] {{
    display: none !important;
}}
.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* ── 메인 로그인 씬 ── */
.login-scene {{
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    {bg_style}
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    overflow: hidden;
    z-index: 99;
}}

/* 이미지 위 어두운 오버레이 (강화) */
.login-scene::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 1;
}}

/* ── 배경 애니메이션: 둥둥 떠다니는 원형 입자 ── */
.bg-orb {{
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.15;
    z-index: 1;
    animation: orb-float 20s infinite alternate;
}}
.orb-1 {{ width: 400px; height: 400px; background: var(--poke-blue); top: -100px; left: -100px; }}
.orb-2 {{ width: 300px; height: 300px; background: var(--poke-red); bottom: -50px; right: -50px; animation-delay: -5s; }}
.orb-3 {{ width: 250px; height: 250px; background: var(--poke-yellow); top: 50%; left: 80%; animation-delay: -10s; }}

@keyframes orb-float {{
    0% {{ transform: translate(0, 0) scale(1); }}
    100% {{ transform: translate(50px, 50px) scale(1.2); }}
}}

/* ── 로그인 카드 (pk-card 스타일 이식) ── */
.login-card {{
    position: relative;
    z-index: 10;
    width: 440px;
    padding: 50px 40px;
    background: var(--glass-bg);
    backdrop-filter: blur(12px) saturate(180%);
    -webkit-backdrop-filter: blur(12px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 30px;
    box-shadow: 0 40px 100px rgba(0, 0, 0, 0.6);
    text-align: center;
    transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    animation: card-reveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

.login-card:hover {{
    transform: translateY(-5px);
}}

@keyframes card-reveal {{
    from {{ opacity: 0; transform: translateY(40px) scale(0.97); }}
    to   {{ opacity: 1; transform: translateY(0)   scale(1);    }}
}}

/* ── 몬스터볼 아이콘 애니메이션 ── */
.card-logo {{
    width: 90px;
    margin: 0 auto 30px;
    filter: drop-shadow(0 0 15px rgba(255, 75, 75, 0.4));
    animation: logo-bounce 4s ease-in-out infinite;
}}

@keyframes logo-bounce {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-10px); }}
}}

/* ── 텍스트 스타일 (detail_styles 스타일 이식) ── */
.login-title {{
    font-size: 38px;
    font-weight: 900;
    color: #FFCB05 !important;
    margin-bottom: 12px;
    letter-spacing: -0.5px;
    text-shadow: 0 0 20px rgba(255, 203, 5, 0.5),
                 0 4px 10px rgba(0, 0, 0, 0.8);
    -webkit-text-stroke: 1px rgba(0, 0, 0, 0.5);
}}

.login-subtitle {{
    font-size: 15px;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 40px;
    line-height: 1.8;
    font-weight: 500;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}}

.user-name {{
    font-size: 30px;
    font-weight: 900;
    color: #ffffff !important;
    margin-bottom: 8px;
    text-shadow: 0 4px 15px rgba(0, 0, 0, 0.9), 0 0 10px rgba(255,255,255,0.2);
}}

.user-id {{
    font-size: 16px;
    color: var(--poke-yellow);
    font-weight: 800;
    opacity: 1;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}}

/* ── 메인 이동 버튼 ── */
.main-nav-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #2a75bb 0%, #1c4d8c 100%);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 14px;
    color: #fff !important;
    font-weight: 800;
    font-size: 15px;
    text-decoration: none !important;
    transition: all 0.3s ease;
    margin-top: 15px;
    box-shadow: 0 8px 20px rgba(42, 117, 187, 0.3);
}}
.main-nav-btn:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 25px rgba(42, 117, 187, 0.5);
    filter: brightness(1.1);
}}

/* ── GitHub 버튼 ── */
.github-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    width: 100%;
    padding: 16px;
    background: linear-gradient(135deg, #24292e 0%, #1a1e22 100%);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    color: #fff !important;
    font-weight: 700;
    font-size: 16px;
    text-decoration: none !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}}
.github-btn:hover {{
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.5);
    border-color: rgba(255, 255, 255, 0.3);
}}

/* ── 혜택 배지 ── */
.benefit-row {{
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 35px;
    flex-wrap: wrap;
}}
.benefit-tag {{
    font-size: 12px;
    font-weight: 700;
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 100px;
    color: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
}}

/* ── 프로필 카드 관련 ── */
.profile-box {{
    margin-bottom: 30px;
}}
.avatar-wrap {{
    width: 100px; height: 100px;
    margin: 0 auto 20px;
    border-radius: 50%;
    padding: 4px;
    background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
    box-shadow: 0 0 30px rgba(0, 210, 255, 0.3);
}}
.avatar-img {{
    width: 100%; height: 100%;
    border-radius: 50%;
    border: 3px solid #080416;
}}

/* ── 로딩 화면 스타일 ── */
.loading-screen {{
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(10px);
}}
.loader-ball {{
    width: 80px;
    height: 80px;
    margin-bottom: 30px;
    animation: loader-spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}}
@keyframes loader-spin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}
.loading-text {{
    color: var(--poke-yellow);
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    animation: text-pulse 1.5s ease-in-out infinite;
}}
@keyframes text-pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(0.95); }}
}}
</style>
"""

POKEBALL_SVG = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" class="card-logo">
  <circle cx="50" cy="50" r="48" fill="#fff" stroke="#000" stroke-width="4"/>
  <path d="M2 50 A48 48 0 0 1 98 50" fill="#f00"/>
  <circle cx="50" cy="50" r="12" fill="#fff" stroke="#000" stroke-width="6"/>
  <circle cx="50" cy="50" r="4" fill="#000"/>
  <path d="M2 50 H38 M62 50 H98" stroke="#000" stroke-width="4"/>
</svg>
"""

FLOATING_SPRITES_HTML = """
<div class="floating-sprites">
    <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/25.gif" style="position:absolute; top:15%; left:10%; width:60px; opacity:0.3;">
    <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/133.gif" style="position:absolute; bottom:20%; right:15%; width:50px; opacity:0.2;">
</div>
"""
