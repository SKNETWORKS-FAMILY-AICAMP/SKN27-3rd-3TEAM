import os
import base64
import streamlit as st

def get_base64_img(file_name):
    # 탐색 우선 순위: 1. 배경폴더, 2. 캐릭터폴더, 3. 기본이미지폴더
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subfolders = ["main_background", "main_character", ""]
    
    for sub in subfolders:
        if sub:
            path = os.path.join(base_dir, "img", sub, file_name)
        else:
            path = os.path.join(base_dir, "img", file_name)
            
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

def inject_mini_game_style():
    bg_img = get_base64_img("minigame2_background.png")
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

    :root {{
        --glass-bg: rgba(20, 20, 20, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
        --poke-red: #E33535;
    }}

    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
        background: url('{bg_img}') center/cover no-repeat fixed !important;
        background-color: #000000 !important;
    }}

    [data-testid="stAppViewBlockContainer"], .main {{ background-color: transparent !important; }}
    .game-container {{ max-width: 1400px; margin: 0 auto; padding: 10px 20px; text-align: center; }}

    .game-card {{
        background: var(--glass-bg); backdrop-filter: blur(20px); border: 1px solid var(--glass-border);
        border-radius: 40px; width: 95%; margin: 0 auto; padding: 40px 20px 65px;
        display: flex; flex-direction: column; align-items: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer; position: relative; overflow: hidden;
        box-shadow: 0 30px 100px rgba(0,0,0,0.6);
    }}

    div[data-testid="stColumn"]:hover .game-card {{
        transform: translateY(-15px) scale(1.02);
        border-color: var(--poke-red);
        box-shadow: 0 30px 80px rgba(227, 53, 53, 0.3);
    }}

    .game-card img {{ width: 250px; height: 250px; object-fit: contain; margin-bottom: 15px; filter: drop-shadow(0 15px 35px rgba(0,0,0,0.4)); }}
    .game-title {{ font-family: 'Outfit', sans-serif; font-size: 2.0rem; font-weight: 900; color: #fff; margin-bottom: 5px; }}
    .game-desc {{ font-family: 'Inter', sans-serif; color: #ccc; font-size: 1.0rem; line-height: 1.5; opacity: 0; transform: translateY(10px); transition: all 0.5s ease; }}
    div[data-testid="stColumn"]:hover .game-desc {{ opacity: 1; transform: translateY(0); margin-top: 20px; }}

    .header-card {{ background: var(--glass-bg); backdrop-filter: blur(15px); border: 1px solid var(--glass-border); border-radius: 25px; padding: 20px 60px; display: inline-block; margin-bottom: 45px; }}

    /* Overlay Button Click */
    [data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div {{ position: relative !important; height: 100%; }}
    [data-testid="stHorizontalBlock"] div[data-testid="stColumn"] .element-container:has(button) {{
        position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important; z-index: 1000 !important; margin: 0 !important;
    }}
    [data-testid="stHorizontalBlock"] div[data-testid="stColumn"] button {{
        width: 100% !important; height: 100% !important; min-height: 350px !important; opacity: 0 !important; cursor: pointer !important;
    }}
    </style>
    """, unsafe_allow_html=True)
