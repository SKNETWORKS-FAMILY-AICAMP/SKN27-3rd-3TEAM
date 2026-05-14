def get_landing_css(bg: dict) -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

:root {{
    --poke-yellow: #FFCB05;
    --poke-blue: #2A75BB;
    --glass-bg: rgba(15, 15, 15, 0.45);
    --glass-border: rgba(255, 255, 255, 0.12);
}}

.stApp {{ background-color: #050505; }}

html, body, [data-testid="stAppViewContainer"], .stApp {{
    background-color: #000000 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

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

/* ── Global Section Layout ── */
.full-section {{
    width: 100%;
    padding: clamp(30px, 5vw, 60px) 4%;
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
    background-attachment: fixed;
    box-sizing: border-box;
    flex-shrink: 0;
}}

/* ── Scanline & Grid Overlay ── */
.full-section::after {{
    content: ''; position: absolute; inset: 0;
    background:
        linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%),
        linear-gradient(90deg, rgba(255, 0, 0, 0.02), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.02));
    background-size: 100% 4px, 3px 100%;
    pointer-events: none;
    z-index: 2;
}}

.full-section::before {{
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.7) 100%);
    z-index: 1;
}}

/* ── Section Backgrounds ── */
.sec-hero        {{ background: url('{bg["main"]}')        center/cover no-repeat fixed; }}
.sec-grass       {{ background: url('{bg["pokedex"]}')     center/cover no-repeat fixed; }}
.sec-fire        {{ background: url('{bg["battle"]}')      center/cover no-repeat fixed; }}
.sec-psychic     {{ background: url('{bg["chatbot"]}')     center/cover no-repeat fixed; }}
.sec-ghost       {{ background: url('{bg["teambuilding"]}') center/cover no-repeat fixed; }}
.sec-water       {{ background: url('{bg["login"]}')       center/cover no-repeat fixed; }}
.sec-electric    {{ background: url('{bg["game1"]}')       center/cover no-repeat fixed; }}
.sec-dragon      {{ background: url('{bg["game2"]}')       center/cover no-repeat fixed; }}
.sec-pipigo      {{ background: url('{bg["pipigo"]}')      center/cover no-repeat fixed; }}

/* ── Holographic Card ── */
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
.text-box  {{ flex: 1.2; z-index: 2; }}
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
}}

.sec-desc {{
    font-family: 'Inter', sans-serif; font-size: clamp(13px, 1.4vw, 19px); line-height: 1.6;
    margin-bottom: clamp(20px, 3vw, 40px); color: #ffffff;
    font-weight: 600; max-width: 550px;
    text-shadow:
        1px 1px 2px #000, -1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000,
        0 5px 15px rgba(0,0,0,1);
}}

/* ── CTA Buttons ── */
.cta-btn {{
    display: inline-flex; align-items: center;
    padding: clamp(12px, 1.4vw, 18px) clamp(24px, 3.5vw, 45px);
    border-radius: 100px;
    font-family: 'Outfit', sans-serif; font-size: clamp(14px, 1.3vw, 18px);
    font-weight: 800; text-decoration: none !important;
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

/* ── Artwork ── */
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
    50%       {{ transform: translateY(-30px) rotate(2deg); }}
}}

/* ── Decor Sprites ── */
.decor-sprite {{
    position: absolute; opacity: 0.7;
    z-index: 5; transition: all 0.4s ease; cursor: pointer;
}}

.decor-sprite:hover {{
    opacity: 1; transform: scale(1.3) rotate(10deg);
    filter: drop-shadow(0 0 25px var(--aura-color, #fff));
}}

/* ── Theme Colors ── */
.sec-hero .sec-badge  {{ color: #000; border-color: #FFCB05; background: #FFCB05 !important; opacity: 1; }}
.sec-hero .sec-title  {{ color: #FFDE00; text-shadow: 2px 2px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 8px 20px rgba(0,0,0,0.9), 0 0 40px rgba(255,222,0,0.6); }}
.sec-hero .cta-btn    {{ background: #FFCB05 !important; color: #000; font-weight: 900; box-shadow: 0 10px 30px rgba(255,203,5,0.4); border-color: #FFCB05; opacity: 1; }}
.sec-hero .main-artwork {{ filter: drop-shadow(0 0 80px rgba(255,203,5,0.5)); width: clamp(220px,38vw,560px); max-height: clamp(200px,36vw,520px); }}

.sec-grass .sec-badge  {{ color: #000; border-color: #4ADE80; background: #4ADE80; }}
.sec-grass .sec-title  {{ color: #4ADE80; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(74,222,128,0.4); }}
.sec-grass .cta-btn    {{ background: #22C55E; color: #fff; box-shadow: 0 10px 30px rgba(34,197,94,0.3); }}
.sec-grass .main-artwork {{ filter: drop-shadow(0 0 80px rgba(34,197,94,0.5)); }}

.sec-fire .sec-badge   {{ color: #fff; border-color: #E11D48; background: #E11D48; }}
.sec-fire .sec-title   {{ color: #FB7185; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(251,113,133,0.4); }}
.sec-fire .cta-btn     {{ background: #E11D48; color: #fff; box-shadow: 0 10px 30px rgba(225,29,72,0.3); }}
.sec-fire .main-artwork {{ filter: drop-shadow(0 0 80px rgba(225,29,72,0.5)); }}

.sec-psychic .sec-badge  {{ color: #fff; border-color: #9333EA; background: #9333EA; }}
.sec-psychic .sec-title  {{ color: #C084FC; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(192,132,252,0.4); }}
.sec-psychic .cta-btn    {{ background: #9333EA; color: #fff; box-shadow: 0 10px 30px rgba(147,51,234,0.3); }}
.sec-psychic .main-artwork {{ filter: drop-shadow(0 0 80px rgba(147,51,234,0.6)); }}

.sec-ghost .sec-badge  {{ color: #fff; border-color: #4F46E5; background: #4F46E5; }}
.sec-ghost .sec-title  {{ color: #818CF8; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(129,140,248,0.4); }}
.sec-ghost .cta-btn    {{ background: #4F46E5; color: #fff; box-shadow: 0 10px 30px rgba(79,70,229,0.3); }}
.sec-ghost .main-artwork {{ filter: drop-shadow(0 0 80px rgba(79,70,229,0.6)); }}

.sec-water .sec-badge  {{ color: #fff; border-color: #38BDF8; background: #0284C7; }}
.sec-water .sec-title  {{ color: #38BDF8; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(56,189,248,0.4); }}
.sec-water .cta-btn    {{ background: #0284C7; color: #fff; box-shadow: 0 10px 30px rgba(2,132,199,0.3); }}
.sec-water .main-artwork {{ filter: drop-shadow(0 0 80px rgba(56,189,248,0.6)); }}

.sec-electric .sec-badge  {{ color: #000; border-color: #FACC15; background: #FACC15; }}
.sec-electric .sec-title  {{ color: #FDE047; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(253,224,71,0.4); }}
.sec-electric .cta-btn    {{ background: #CA8A04; color: #fff; box-shadow: 0 10px 30px rgba(202,138,4,0.3); }}
.sec-electric .main-artwork {{ filter: drop-shadow(0 0 80px rgba(250,204,21,0.6)); }}

.sec-dragon .sec-badge  {{ color: #fff; border-color: #F97316; background: #EA580C; }}
.sec-dragon .sec-title  {{ color: #FB923C; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(249,115,22,0.4); }}
.sec-dragon .cta-btn    {{ background: #EA580C; color: #fff; box-shadow: 0 10px 30px rgba(234,88,12,0.3); }}
.sec-dragon .main-artwork {{ filter: drop-shadow(0 0 80px rgba(249,115,22,0.6)); }}

.sec-pipigo .sec-badge  {{ color: #000; border-color: #A3E635; background: #A3E635; }}
.sec-pipigo .sec-title  {{ color: #BEF264; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 10px 30px rgba(0,0,0,1), 0 0 40px rgba(190,242,100,0.4); }}
.sec-pipigo .cta-btn    {{ background: #A3E635; color: #000; font-weight: 900; box-shadow: 0 10px 30px rgba(163,230,53,0.3); border-color: #A3E635; }}
.sec-pipigo .main-artwork {{ filter: drop-shadow(0 0 80px rgba(163,230,53,0.6)); width: 320px; }}

/* ── Reveal Animations ── */
.js-ready .reveal-up    {{ transform: translateY(80px);  opacity: 0; transition: all 1.2s cubic-bezier(0.16, 1, 0.3, 1); }}
.js-ready .reveal-left  {{ transform: translateX(-80px); opacity: 0; transition: all 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.2s; }}
.js-ready .reveal-right {{ transform: translateX(80px);  opacity: 0; transition: all 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.2s; }}

.js-ready .in-view .reveal-up,
.js-ready .in-view .reveal-left,
.js-ready .in-view .reveal-right {{ transform: translate(0); opacity: 1; }}

@media (max-width: 1024px) {{
    .section-inner {{ flex-direction: column !important; padding: 60px 30px; text-align: center; }}
    .text-box  {{ margin-bottom: 50px; order: 2; }}
    .visual-box {{ order: 1; }}
    .sec-title {{ font-size: 40px; }}
}}
</style>
"""
