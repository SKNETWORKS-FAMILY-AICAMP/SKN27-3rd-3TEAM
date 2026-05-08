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

    # 배경 스타일 설정
    if bg_data:
        # linear-gradient 투명도를 0.75에서 0.3으로 낮춰 이미지를 더 선명하게 표시
        bg_style = f"""
            background-image: linear-gradient(rgba(240, 240, 240, 0.5), rgba(240, 240, 240, 0.5)), url('{bg_data}') !important;
            background-size: cover !important;
            background-attachment: fixed !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
        """
    else:
        # 기본 배경
        bg_style = """
            background-color: #e8e8e8 !important;
            background-image: radial-gradient(circle, #d0d0d0 1px, transparent 1px) !important;
            background-size: 24px 24px !important;
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

:root {{
    --poke-yellow: #FFCB05;
    --poke-blue: #2A75BB;
    --glass-bg: rgba(15, 15, 15, 0.65);
    --glass-border: rgba(255, 255, 255, 0.12);
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

.pk-cta {{
    display: block; background: var(--poke-yellow); color: #000 !important;
    text-align: center; padding: 18px 30px;
    border-radius: 12px; font-size: 1.1rem; font-weight: 800;
    text-decoration: none !important; margin-top: 10px;
    transition: all 0.3s ease;
    font-family: 'Outfit', sans-serif;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
.pk-cta:hover {{ 
    background: #fff !important; 
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(255, 203, 5, 0.3);
}}

/* ── Evolution & Forms Sections ── */
.evo-section, .forms-section {{
    max-width: 1000px; margin: 0 auto 40px auto;
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 24px; padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
    font-family: 'Outfit', sans-serif;
}}
.evo-title, .forms-title {{
    font-size: 1.2rem; font-weight: 800;
    margin-bottom: 30px; display: flex; align-items: center; gap: 10px;
    color: #fff; text-transform: uppercase; letter-spacing: 1.5px;
}}
.forms-grid {{
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 20px;
    flex-wrap: wrap;
}}
.evo-card, .form-card {{
    text-align: center; border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    border-radius: 18px; padding: 20px; width: 150px;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
}}
.evo-card:hover, .form-card:hover {{ 
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-8px) scale(1.05);
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 15px 30px rgba(0,0,0,0.4);
}}
.evo-img, .form-img {{ 
    width: 110px; height: 110px; object-fit: contain; 
    filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2));
}}
.evo-arrow {{ color: rgba(255, 255, 255, 0.2); font-size: 24px; }}

.variety-section {{
    max-width: 1000px; margin: 0 auto 20px auto;
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 20px 30px;
    display: flex; flex-direction: column; gap: 12px;
    font-family: 'Outfit', sans-serif;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}}
.variety-title {{
    font-size: 0.95rem; font-weight: 800; color: #fff;
    display: flex; align-items: center; gap: 8px;
    text-transform: uppercase; letter-spacing: 1px;
}}
.variety-list {{
    display: flex; flex-wrap: wrap; gap: 8px;
}}
.variety-btn {{
    background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 8px 20px; border-radius: 25px;
    font-size: 0.9rem; color: #fff !important; text-decoration: none !important;
    transition: all 0.3s ease; cursor: pointer;
    display: inline-block;
}}
.variety-btn:visited {{ color: #fff !important; }}
.variety-btn:hover {{ background: rgba(255, 255, 255, 0.2); color: #fff !important; }}
.variety-btn.active {{
    background: var(--poke-yellow); color: #000 !important;
    font-weight: 800;
}}

.form-card.active {{ border: 2px solid var(--poke-yellow); background: rgba(255, 203, 5, 0.05); }}
.form-name {{ font-weight: 700; font-size: 0.95rem; color: #fff; margin-top: 10px; line-height: 1.2; }}
.form-label {{ 
    position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
    background: var(--poke-yellow); color: #000; font-size: 0.7rem; padding: 3px 12px;
    border-radius: 12px; font-weight: 900; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}}
</style>
"""
