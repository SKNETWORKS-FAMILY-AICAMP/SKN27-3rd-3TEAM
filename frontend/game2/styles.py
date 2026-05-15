import streamlit as st

def inject_game2_styles(bg_img: str = "") -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@400;600;800&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
    background: url('{bg_img}') center/cover no-repeat fixed !important;
    background-color: #000000 !important;
}}

[data-testid="stAppViewBlockContainer"], .main {{ 
    background-color: transparent !important; 
}}

/* iframe styling */
iframe {{
    border-radius: 20px !important;
    background: transparent !important;
}}

/* Remove wrapping card effect as requested */
[data-testid="stVerticalBlock"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )
