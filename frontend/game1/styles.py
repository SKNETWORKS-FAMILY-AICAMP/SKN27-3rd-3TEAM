import os
import base64
import streamlit as st

def get_base64_img(file_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

def inject_game_1_style():
    bg_img = get_base64_img("mini_game.png")
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@400;600;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
        background: url('{bg_img}') center/cover no-repeat fixed !important;
        background-color: #000000 !important;
    }}

    [data-testid="stAppViewBlockContainer"], .main {{ background-color: transparent !important; }}
    .sil-main-card, .btn-marker {{ position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }}

    [data-testid="stVerticalBlock"]:has(> .element-container .sil-main-card) {{
        background: linear-gradient(135deg, rgba(42, 117, 187, 0.2) 0%, rgba(20, 20, 20, 0.8) 50%, rgba(227, 53, 53, 0.1) 100%) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 35px !important;
        padding: 1rem 3rem !important;
        box-shadow: 0 40px 100px rgba(0,0,0,0.7) !important;
        margin-top: 90px !important;
    }}

    [data-testid="stTextInput"] {{
        width: 55% !important;
        margin: 30px auto 0 !important;
    }}
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input {{
        background-color: #000000 !important;
        border-color: #E33535 !important;
        border-radius: 15px !important;
    }}
    [data-testid="stTextInput"] [data-baseweb="input"] {{
        border: 3px solid #E33535 !important;
        min-height: 55px !important;
    }}
    [data-testid="stTextInput"] input {{ color: #ffffff !important; font-family: 'Outfit'; font-weight: 700; font-size: 1.2rem !important; text-align: center !important; }}

    div[data-testid="stColumn"]:has(.btn-marker) button {{
        border-radius: 12px !important; height: 45px !important; width: 100% !important;
        border: 2px solid #E33535 !important;
    }}
    div[data-testid="stColumn"]:has(.btn-marker) button p {{ font-family: 'Outfit'; font-weight: 800; font-size: 1rem !important; }}

    div[data-testid="stColumn"]:has(.btn-hint) button {{ background-color: #ffffff !important; }}
    div[data-testid="stColumn"]:has(.btn-hint) button p {{ color: #000000 !important; }}
    div[data-testid="stColumn"]:has(.btn-giveup) button {{ background-color: #000000 !important; }}
    div[data-testid="stColumn"]:has(.btn-giveup) button p {{ color: #ffffff !important; }}
    div[data-testid="stColumn"]:has(.btn-next) button {{ background-color: #ffffff !important; }}
    div[data-testid="stColumn"]:has(.btn-next) button p {{ color: #000000 !important; }}

    .sil-hint-box {{
        background: rgba(10, 10, 10, 0.8) !important;
        border: 1px solid #E33535 !important;
        border-left: 5px solid #E33535 !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.4) !important;
    }}

    .sil-hint-box p {{
        color: #ffffff !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }}

    .image-glow-ring {{
        background: rgba(227, 53, 53, 0.05); border-radius: 50%; padding: 25px;
        backdrop-filter: blur(15px); border: 1px solid rgba(227, 53, 53, 0.2);
        box-shadow: inset 0 0 50px rgba(0,0,0,0.6), 0 0 50px rgba(227, 53, 53, 0.4);
        display: inline-block;
    }}

    .silhouette-img {{ filter: brightness(0); transform: scale(1.0); }}
    .silhouette-img.revealed {{
        filter: brightness(1) drop-shadow(0 0 20px rgba(255,255,255,0.4));
        transform: scale(1.1); transition: filter 1s ease-in-out, transform 0.6s ease;
    }}
    </style>
    """, unsafe_allow_html=True)
