import streamlit as st
import os
import sys

# Ensure frontend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import inject_common_ui
from mypage.styles import inject_mypage_styles
from mypage.ui import show

st.set_page_config(
    page_title="마이페이지",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def main():
    # 1. 공통 UI 주입
    inject_common_ui()
    
    # 2. 스타일 주입
    inject_mypage_styles()
    
    # 3. 메인 UI 렌더링
    show()

if __name__ == "__main__":
    main()
