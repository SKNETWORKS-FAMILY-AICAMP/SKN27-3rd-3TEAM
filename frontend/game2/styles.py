import streamlit as st


def inject_game2_styles(bg_img: str = "") -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Noto+Sans+KR:wght@400;700;900&display=swap');

html,body,[data-testid="stAppViewContainer"],[data-testid="stHeader"],.stApp{{
    background:url('{bg_img}') center/cover no-repeat fixed !important;
    background-color:#000 !important;
}}

[data-testid="stWidgetLabel"] p{{
    color:#CC88FF !important;
    font-weight:700 !important;
    font-size:.85rem !important;
}}

div[data-testid="stSlider"] div[role="slider"]{{
    background:#FF00FF !important;
}}

div[data-testid="stSlider"] .stSlider > div > div > div{{
    background:linear-gradient(90deg,#FF00FF,#7700EE) !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )
