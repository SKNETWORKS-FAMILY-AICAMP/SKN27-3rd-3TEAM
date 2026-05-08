import streamlit as st
import base64
import os

def get_base64_img(file_name):
    # 도커 컨테이너 내부 경로(/app)와 로컬 경로를 모두 고려한 경로 탐색
    # detail_styles.py 위치: /app/pages/style/detail_styles.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 여러 가능한 경로 후보들 (img/bg 폴더 찾기)
    possible_paths = [
        os.path.join(current_dir, "..", "..", "img", "bg", file_name),  # /app/img/bg/
        os.path.join(os.getcwd(), "frontend", "img", "bg", file_name), # 로컬 실행 환경
        os.path.join(os.getcwd(), "img", "bg", file_name),             # 도커 실행 환경
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

def get_detail_styles(main_type="노말"):
    # 영어 이름과 한글 이름 매핑 (파일명이 어떤 것이든 대응할 수 있도록)
    type_map = {
        "fire": "불꽃", "water": "물", "grass": "풀", "electric": "전기",
        "ice": "얼음", "fighting": "격투", "poison": "독", "ground": "땅",
        "flying": "비행", "psychic": "에스퍼", "bug": "벌레", "rock": "바위",
        "ghost": "고스트", "dragon": "드래곤", "dark": "악", "steel": "강철",
        "fairy": "페어리", "normal": "노말"
    }
    
    # 1. 원본 타입명으로 시도 (예: bg_불꽃.png 또는 bg_fire.png)
    bg_data = get_base64_img(f"bg_{main_type}.png")
    
    # 2. 실패 시 매핑된 이름으로 시도
    if not bg_data:
        # 영어 -> 한글 변환 시도
        if main_type.lower() in type_map:
            bg_data = get_base64_img(f"bg_{type_map[main_type.lower()]}.png")
        # 한글 -> 영어 변환 시도 (역매핑)
        else:
            rev_map = {v: k for k, v in type_map.items()}
            if main_type in rev_map:
                bg_data = get_base64_img(f"bg_{rev_map[main_type]}.png")

    # 타입별 대표 색상 맵핑
    TYPE_COLORS = {
        "불꽃": "rgba(255, 68, 34, 0.15)", "물": "rgba(51, 153, 255, 0.15)", "풀": "rgba(119, 204, 85, 0.15)", 
        "전기": "rgba(255, 204, 51, 0.15)", "얼음": "rgba(102, 204, 255, 0.15)", "격투": "rgba(187, 85, 68, 0.15)", 
        "독": "rgba(170, 85, 153, 0.15)", "땅": "rgba(221, 187, 85, 0.15)", "비행": "rgba(136, 153, 255, 0.15)", 
        "에스퍼": "rgba(255, 85, 153, 0.15)", "벌레": "rgba(170, 187, 34, 0.15)", "바위": "rgba(187, 170, 102, 0.15)", 
        "고스트": "rgba(102, 102, 187, 0.15)", "드래곤": "rgba(119, 102, 238, 0.15)", "악": "rgba(119, 85, 68, 0.15)", 
        "강철": "rgba(170, 170, 187, 0.15)", "페어리": "rgba(238, 153, 238, 0.15)", "노말": "rgba(170, 170, 153, 0.15)"
    }
    
    # 타입별 테두리/포인트 색상
    TYPE_POINTS = {
        "불꽃": "#ff4422", "물": "#3399ff", "풀": "#77cc55", "전기": "#ffcc33",
        "얼음": "#66ccff", "격투": "#bb5544", "독": "#aa5599", "땅": "#ddbb55",
        "비행": "#8899ff", "에스퍼": "#ff5599", "벌레": "#aabb22", "바위": "#bbaa66",
        "고스트": "#6666bb", "드래곤": "#7766ee", "악": "#775544", "강철": "#aaaabb",
        "페어리": "#ee99ee", "노말": "#aaaa99"
    }

    type_aura = TYPE_COLORS.get(main_type, "rgba(255, 255, 255, 0.05)")
    type_point = TYPE_POINTS.get(main_type, "#ffffff")

    # 배경 스타일 설정
    if bg_data:
        # linear-gradient 투명도를 0.75에서 0.3으로 낮춰 이미지를 더 선명하게 표시
        bg_style = f"""
            background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('{bg_data}') !important;
            background-size: cover !important;
            background-attachment: fixed !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
        """
    else:
        # 기본 배경
        bg_style = """
            background-color: #050505 !important;
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

:root {{
    --poke-yellow: #FFCB05;
    --poke-blue: #2A75BB;
    --glass-bg: rgba(15, 15, 15, 0.65);
    --glass-border: rgba(255, 255, 255, 0.12);
    --type-aura: {type_aura};
    --type-point: {type_point};
}}

[data-testid="collapsedControl"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* 최상위 컨테이너에 배경 적용 */
.stApp, [data-testid="stAppViewContainer"] {{
    {bg_style}
    background-color: #050505 !important;
}}

.pk-nav {{
    background-color: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: stretch;
    min-height: 72px;
    width: 100vw;
    margin-left: calc(50% - 50vw);
    margin-top: 0;
    margin-bottom: 28px;
    font-family: 'Outfit', sans-serif;
    border-bottom: 1px solid var(--glass-border);
}}
.pk-nav-left, .pk-nav-right {{
    display: flex;
    align-items: center;
    flex: 1;
    padding: 0 40px;
    text-decoration: none !important;
    color: white !important;
    gap: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
}}
.pk-nav-left:hover, .pk-nav-right:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
.pk-nav-right {{ justify-content: flex-end; text-align: right; }}
.pk-nav-sep {{ width: 1px; background: rgba(255, 255, 255, 0.1); margin: 14px 0; flex-shrink: 0; }}
.nav-circle {{
    width: 38px; height: 38px; border-radius: 50%;
    border: 2px solid rgba(255, 255, 255, 0.3);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; color: white;
}}
.pk-nav-name {{ font-size: 0.95rem; font-weight: 600; }}
.pk-nav-num  {{ font-size: 0.78rem; color: rgba(255, 255, 255, 0.5); }}

/* ── Premium Glass Card ── */
.pk-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(12px) saturate(180%);
    -webkit-backdrop-filter: blur(12px) saturate(180%);
    border: 1px solid var(--glass-border);
    border-radius: 30px;
    box-shadow: 0 40px 100px rgba(0,0,0,0.6);
    max-width: 1000px;
    margin: 0 auto 36px auto;
    display: flex;
    overflow: hidden;
    font-family: 'Inter', sans-serif;
    transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}
.pk-card:hover {{ transform: translateY(-5px); }}

.pk-card-left {{
    width: 380px; flex-shrink: 0;
    background: rgba(255, 255, 255, 0.03);
    display: flex; align-items: center; justify-content: center;
    padding: 60px 40px;
    position: relative;
}}
.pk-card-left::before {{
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, transparent 70%);
    pointer-events: none;
}}

.pk-card-img {{
    width: 300px; height: 300px;
    object-fit: contain;
    filter: drop-shadow(0 20px 40px rgba(0,0,0,0.4));
    animation: float 6s ease-in-out infinite;
}}

@keyframes float {{ 
    0%, 100% {{ transform: translateY(0); }} 
    50% {{ transform: translateY(-15px); }} 
}}

.pk-card-right {{
    flex: 1; padding: 48px 50px 60px 50px;
    display: flex; flex-direction: column; gap: 20px;
    background: rgba(0, 0, 0, 0.2);
}}
.pk-id   {{ color: var(--poke-yellow); font-size: 1.1rem; font-weight: 800; font-family: 'Outfit', sans-serif; }}
.pk-name {{ 
    font-family: 'Outfit', sans-serif;
    font-size: 3.2rem; font-weight: 900; color: #fff; margin: 0; line-height: 1;
    text-shadow: 0 4px 10px rgba(0,0,0,0.3);
}}

.pk-badges {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.v-badge {{
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    padding: 6px 16px; font-size: 0.85rem; color: #eee; font-weight: 600;
}}
.v-check {{
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--poke-yellow); display: inline-flex; align-items: center;
    justify-content: center; font-size: 11px; color: #000; flex-shrink: 0; font-weight: 900;
}}

.pk-desc {{ 
    color: rgba(255, 255, 255, 0.8); 
    font-size: 1.05rem; line-height: 1.8; 
    font-weight: 400;
}}

.pk-stats {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.05);
}}
.pk-stat-cell {{
    padding: 18px 22px;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}}
.pk-stat-cell:nth-child(3n)  {{ border-right: none; }}
.pk-stat-cell:nth-child(n+4) {{ border-bottom: none; }}
.pk-stat-label {{ color: rgba(255, 255, 255, 0.4); font-size: 0.8rem; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; }}
.pk-stat-value {{ color: #fff; font-weight: 600; font-size: 1rem; display: flex; flex-wrap: wrap; align-items: center; }}

.gender-male   {{ color: #60a5fa; font-size: 1.4rem; margin-right: 6px; }}
.gender-female {{ color: #f472b6; font-size: 1.4rem; }}

.ability-row {{ display: flex; flex-direction: column; gap: 5px; }}
.ability-item {{ display: flex; align-items: center; gap: 8px; }}
.ability-help {{
    width: 18px; height: 18px; border-radius: 50%;
    background: rgba(255, 255, 255, 0.2); color: white; font-size: 11px;
    display: inline-flex; align-items: center; justify-content: center;
    cursor: help; flex-shrink: 0;
}}

.back-btn {{
    background: var(--type-point);
    color: #fff !important; font-weight: 800; font-size: 1.1rem;
    padding: 15px 40px; border-radius: 12px;
    text-decoration: none !important; display: flex; align-items: center; justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3), 0 0 20px var(--type-aura);
    width: 100%; border: none; cursor: pointer;
    text-transform: uppercase; letter-spacing: 1px;
}}
.back-btn:hover {{ 
    transform: translateY(-3px); 
    box-shadow: 0 15px 35px rgba(0,0,0,0.4), 0 0 30px var(--type-aura);
    filter: brightness(1.1);
}}

/* ── Evolution & Forms Sections ── */
.evo-section, .forms-section {{
    max-width: 1000px; margin: 0 auto 40px auto;
    background: linear-gradient(135deg, var(--glass-bg), var(--type-aura));
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 24px; padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.4), inset 0 0 40px rgba(255,255,255,0.02);
    font-family: 'Outfit', sans-serif;
    position: relative;
    overflow: hidden;
}}
.evo-section::after, .forms-section::after {{
    content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle, var(--type-aura) 0%, transparent 70%);
    opacity: 0.3; pointer-events: none; z-index: 0;
}}

.evo-title, .forms-title {{
    font-size: 1.3rem; font-weight: 900;
    margin-bottom: 30px; display: flex; align-items: center; gap: 12px;
    color: #fff; text-transform: uppercase; letter-spacing: 2px;
    position: relative; z-index: 1;
}}
.evo-title::before, .forms-title::before {{
    content: ''; width: 6px; height: 24px; background: var(--type-point); border-radius: 3px;
    box-shadow: 0 0 15px var(--type-point);
}}

.forms-grid {{
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 20px;
    flex-wrap: wrap;
    position: relative; z-index: 1;
}}
.evo-card, .form-card {{
    text-align: center; 
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(5px);
    border-radius: 20px; padding: 22px 15px; width: 190px; min-height: 265px;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative; z-index: 1;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.02);
}}
.evo-card::before, .form-card::before {{
    content: ''; position: absolute; inset: 0; border-radius: 20px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(255,255,255,0.2), var(--type-point));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
}}
.evo-card:hover, .form-card:hover {{ 
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-8px) scale(1.05);
    border-color: var(--type-point);
    box-shadow: 0 15px 30px rgba(0,0,0,0.5), 0 0 20px var(--type-aura);
}}
.evo-img, .form-img {{ 
    width: 135px; height: 135px; object-fit: contain; 
    filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2));
}}
.evo-arrow {{ color: var(--type-point); font-size: 24px; opacity: 0.6; }}

.evo-type-badge {{ border-radius: 4px; padding: 3px 8px; font-size: 0.65rem; font-weight: 700; color: #fff; }}
.evo-type-normal   {{ background: #A8A77A; }}
.evo-type-fire     {{ background: #EE8130; }}
.evo-type-water    {{ background: #6390F0; }}
.evo-type-electric {{ background: #F7D02C; color: #000; }}
.evo-type-grass    {{ background: #7AC74C; }}
.evo-type-ice      {{ background: #96D9D9; color: #000; }}
.evo-type-fighting {{ background: #C22E28; }}
.evo-type-poison   {{ background: #A33EA1; }}
.evo-type-ground   {{ background: #E2BF65; color: #000; }}
.evo-type-flying   {{ background: #A98FF3; }}
.evo-type-psychic  {{ background: #F95587; }}
.evo-type-bug      {{ background: #A6B91A; }}
.evo-type-rock     {{ background: #B6A136; }}
.evo-type-ghost    {{ background: #735797; }}
.evo-type-dragon   {{ background: #6F35FC; }}
.evo-type-steel    {{ background: #B7B7CE; color: #000; }}
.evo-type-fairy    {{ background: #D685AD; }}
.evo-type-dark     {{ background: #705746; }}

.variety-section {{
    max-width: 1000px; margin: 0 auto 20px auto;
    background: linear-gradient(90deg, var(--glass-bg), var(--type-aura));
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 20px 30px;
    display: flex; flex-direction: column; gap: 12px;
    font-family: 'Outfit', sans-serif;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}}
.variety-title {{
    font-size: 1rem; font-weight: 900; color: #fff;
    display: flex; align-items: center; gap: 10px;
    text-transform: uppercase; letter-spacing: 1.5px;
}}
.variety-title::before {{
    content: ''; width: 4px; height: 18px; background: var(--type-point); border-radius: 2px;
}}

.variety-list {{
    display: flex; flex-wrap: wrap; gap: 10px;
}}
.variety-btn {{
    background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 8px 20px; border-radius: 25px;
    font-size: 0.9rem; color: #fff !important; text-decoration: none !important;
    transition: all 0.3s ease; cursor: pointer;
    display: inline-block;
}}
.variety-btn:visited {{ color: #fff !important; }}
.variety-btn:hover {{ 
    background: var(--type-aura); 
    border-color: var(--type-point);
    color: #fff !important; 
    transform: translateY(-2px);
}}
.variety-btn.active {{
    background: var(--type-point); color: #fff !important;
    font-weight: 900;
    box-shadow: 0 0 15px var(--type-aura);
}}

.evo-card.active, .form-card.active {{ border: 2px solid var(--type-point); background: var(--type-aura); }}
.form-name {{ 
    font-weight: 800; font-size: 0.98rem; color: #fff; 
    margin-top: 10px; line-height: 1.2; font-family: 'Outfit', sans-serif;
    word-break: keep-all; overflow-wrap: break-word;
    max-width: 100%;
}}
.form-label {{ 
    position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
    background: var(--type-point); color: #fff; font-size: 0.7rem; padding: 3px 12px;
    border-radius: 12px; font-weight: 900; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}}
</style>
"""
