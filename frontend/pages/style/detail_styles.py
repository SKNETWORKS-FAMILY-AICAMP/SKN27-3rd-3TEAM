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
[data-testid="collapsedControl"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* 최상위 컨테이너에 배경 적용 */
.stApp, [data-testid="stAppViewContainer"] {{
    {bg_style}
}}

.pk-nav {{
    background-color: #2e2e2e;
    display: flex;
    align-items: stretch;
    min-height: 72px;
    width: 100vw;
    margin-left: calc(50% - 50vw);
    margin-top: 0;
    margin-bottom: 28px;
    font-family: sans-serif;
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
    transition: background 0.15s;
}}
.pk-nav-left:hover, .pk-nav-right:hover {{ background-color: #3d3d3d; }}
.pk-nav-right {{ justify-content: flex-end; text-align: right; }}
.pk-nav-sep {{ width: 1px; background: #555; margin: 14px 0; flex-shrink: 0; }}
.nav-circle {{
    width: 38px; height: 38px; border-radius: 50%;
    border: 2px solid #666;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; color: white;
}}
.pk-nav-name {{ font-size: 0.95rem; font-weight: 500; }}
.pk-nav-num  {{ font-size: 0.78rem; color: #aaa; }}

.pk-card {{
    background: white;
    border-radius: 10px;
    border: 2px solid #2e2e2e;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    max-width: 900px;
    margin: 0 auto 36px auto;
    display: flex;
    overflow: hidden;
    font-family: sans-serif;
}}
.pk-card-left {{
    width: 320px; flex-shrink: 0;
    background: #f0f0f0;
    display: flex; align-items: center; justify-content: center;
    padding: 48px 24px;
    background-image: radial-gradient(circle, #ddd 1px, transparent 1px);
    background-size: 18px 18px;
}}
.pk-card-img {{
    width: 250px; height: 250px;
    object-fit: contain;
    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.15));
}}
.pk-card-right {{
    flex: 1; padding: 36px 40px 52px 40px;
    display: flex; flex-direction: column; gap: 14px;
}}
.pk-id   {{ color: #aaa; font-size: 0.88rem; }}
.pk-name {{ font-size: 2.4rem; font-weight: 900; color: #1a1a1a; margin: 0; line-height: 1.1; }}

.pk-badges {{ display: flex; flex-wrap: wrap; gap: 7px; }}
.v-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #efefef; border-radius: 999px;
    padding: 5px 13px; font-size: 0.82rem; color: #555; font-weight: 500;
}}
.v-check {{
    width: 17px; height: 17px; border-radius: 50%;
    background: #bbb; display: inline-flex; align-items: center;
    justify-content: center; font-size: 10px; color: white; flex-shrink: 0;
}}

.pk-desc {{ color: #555; font-size: 0.92rem; line-height: 1.75; }}

.pk-stats {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    overflow: hidden;
}}
.pk-stat-cell {{
    padding: 14px 18px;
    border-right: 1px solid #e8e8e8;
    border-bottom: 1px solid #e8e8e8;
}}
.pk-stat-cell:nth-child(3n)  {{ border-right: none; }}
.pk-stat-cell:nth-child(n+4) {{ border-bottom: none; }}
.pk-stat-label {{ color: #aaa; font-size: 0.77rem; margin-bottom: 7px; }}
.pk-stat-value {{ color: #222; font-weight: 600; font-size: 0.9rem; display: flex; flex-wrap: wrap; align-items: center; }}

.gender-male   {{ color: #4a90d9; font-size: 1.25rem; margin-right: 4px; }}
.gender-female {{ color: #e0507a; font-size: 1.25rem; }}

.ability-row {{ display: flex; flex-direction: column; gap: 3px; }}
.ability-item {{ display: flex; align-items: center; gap: 5px; }}
.ability-help {{
    width: 16px; height: 16px; border-radius: 50%;
    background: #666; color: white; font-size: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    cursor: default; flex-shrink: 0;
}}

.pk-cta {{
    display: block; background: #E3350D; color: white !important;
    text-align: center; padding: 15px 30px;
    border-radius: 6px; font-size: 1rem; font-weight: 700;
    text-decoration: none !important; margin-top: 4px;
    transition: background 0.2s;
}}
.pk-cta:hover {{ background: #c22b09 !important; }}

.evo-section {{
    max-width: 900px; margin: 0 auto 40px auto;
    background: white; border-radius: 16px; padding: 30px 36px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    font-family: sans-serif;
}}
.evo-title {{
    font-size: 1rem; font-weight: 700;
    margin-bottom: 22px; display: flex; align-items: center; gap: 8px;
    color: #1a1a1a;
}}
.evo-chain {{
    display: flex; justify-content: center;
    align-items: center; gap: 16px; flex-wrap: wrap;
}}
.evo-card {{
    text-align: center; border: 1px solid #eee;
    border-radius: 12px; padding: 16px; width: 130px;
    transition: box-shadow 0.2s;
}}
.evo-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
.evo-img   {{ width: 90px; height: 90px; object-fit: contain; }}
.evo-arrow {{ color: #ccc; font-size: 22px; }}

.variety-section {{
    max-width: 900px; margin: 0 auto 20px auto;
    display: flex; flex-direction: column; gap: 10px;
    font-family: sans-serif;
}}
.variety-title {{
    font-size: 0.9rem; font-weight: 700; color: #666;
    display: flex; align-items: center; gap: 6px;
}}
.variety-list {{
    display: flex; flex-wrap: wrap; gap: 8px;
}}
.variety-btn {{
    background: white; border: 1px solid #ddd;
    padding: 6px 16px; border-radius: 20px;
    font-size: 0.85rem; color: #444; text-decoration: none !important;
    transition: all 0.2s; cursor: pointer;
}}
.variety-btn:hover {{ background: #f5f5f5; border-color: #bbb; }}
.variety-btn.active {{
    background: #2e2e2e; color: white; border-color: #2e2e2e;
    font-weight: 600;
}}

.forms-section {{
    max-width: 900px; margin: 0 auto 60px auto;
    background: white; border-radius: 16px; padding: 30px 36px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    font-family: sans-serif;
}}
.forms-title {{
    font-size: 1rem; font-weight: 700;
    margin-bottom: 22px; display: flex; align-items: center; gap: 8px;
    color: #1a1a1a;
}}
.forms-grid {{
    display: flex; justify-content: center;
    align-items: center; gap: 16px; flex-wrap: wrap;
}}
.form-card {{
    text-align: center; border: 1px solid #eee;
    border-radius: 12px; padding: 16px; width: 140px;
    transition: all 0.2s; position: relative;
}}
.form-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.12); transform: translateY(-3px); }}
.form-card.active {{ border: 2px solid #E3350D; background: #fff8f8; }}
.form-img {{ width: 100px; height: 100px; object-fit: contain; }}
.form-name {{ font-weight: 700; font-size: 0.85rem; color: #1a1a1a; margin-top: 8px; line-height: 1.2; }}
.form-label {{ 
    position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
    background: #E3350D; color: white; font-size: 0.65rem; padding: 2px 8px;
    border-radius: 10px; font-weight: 800;
}}
</style>
"""
