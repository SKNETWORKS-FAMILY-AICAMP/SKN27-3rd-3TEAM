import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Ensure frontend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from login.logic import show_login_page

# 환경 변수 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

def main():
    st.set_page_config(
        page_title="트레이너 인증",
        page_icon="https://pokemonkorea.co.kr/img/_con.ico",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    show_login_page()

if __name__ == "__main__":
    main()
