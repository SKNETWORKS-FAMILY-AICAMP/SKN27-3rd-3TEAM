import streamlit as st
import sys
import os
import requests

# Ensure root and frontend are importable (for utils)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
frontend_dir = os.path.join(root_dir, "frontend")

if root_dir not in sys.path:
    sys.path.append(root_dir)
if frontend_dir not in sys.path:
    sys.path.append(frontend_dir)

from utils.ui import inject_common_ui
from utils.pokedex_styles import get_pokedex_styles, render_pokemon_card

# API Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_V1_STR = "/api/v1/pokemon"

# Type mapping for CSS classes
TYPE_MAP = {
    "노말": "normal", "불꽃": "fire", "물": "water", "풀": "grass",
    "전기": "electric", "얼음": "ice", "격투": "fighting", "독": "poison",
    "땅": "ground", "비행": "flying", "에스퍼": "psychic", "벌레": "bug",
    "바위": "rock", "고스트": "ghost", "드래곤": "dragon", "강철": "steel",
    "페어리": "fairy", "악": "dark"
}

st.set_page_config(
    page_title="Pokedex - Pokémon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
)

# Inject common UI
inject_common_ui(spacer=True)
st.write(get_pokedex_styles(), unsafe_allow_html=True)

# Session state for pagination
if "pokemon_limit" not in st.session_state:
    st.session_state.pokemon_limit = 1025

def load_more():
    st.session_state.pokemon_limit += 20

# Main UI
with st.container():

    # Dark Search & Filter Section
    with st.container():
        
        # Search Bar
        search_col, _ = st.columns([1, 0.01])
        with search_col:
            st.session_state.search_query = st.text_input("포켓몬 이름 또는 번호, 특성 키워드를 입력해주세요.", value=st.session_state.get('search_query', ''), placeholder="포켓몬 이름 또는 번호, 특성 키워드를 입력해주세요.", label_visibility="collapsed")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.selectbox("특성", ["전체"], label_visibility="visible")
            st.selectbox("지역", ["전체", "관동", "성도", "호연", "신오", "하나", "칼로스", "알로라", "가라르", "팔데아"], label_visibility="visible")
            
            c1, c2, c3 = st.columns([1, 0.1, 1])
            with c1:
                st.text_input("도감번호 시작", value="1", label_visibility="collapsed")
            with c2:
                st.markdown("<div style='text-align:center; color:white; padding-top:10px;'>-</div>", unsafe_allow_html=True)
            with c3:
                st.text_input("도감번호 끝", value="1025", label_visibility="collapsed")
                
        with col2:
            st.markdown("<span style='color:white; font-size:14px; margin-bottom:10px; display:block;'>타입</span>", unsafe_allow_html=True)
            all_types = list(TYPE_MAP.keys())
            if 'selected_types' not in st.session_state:
                st.session_state.selected_types = []
            st.session_state.selected_types = st.multiselect("타입 선택", all_types, default=st.session_state.selected_types, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 2])
        with btn_col2:
            bc1, bc2 = st.columns(2)
            with bc1:
                st.markdown('<button class="btn-search"><span>검색</span></button>', unsafe_allow_html=True)
            with bc2:
                st.markdown('<button class="btn-reset"><span>초기화</span></button>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # API Data Fetching
    try:
        params = {
            "skip": 0,
            "limit": st.session_state.pokemon_limit,
            "search": st.session_state.search_query if st.session_state.search_query else None
        }
        
        response = requests.get(f"{BACKEND_URL}{API_V1_STR}/", params=params)
        
        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total", 0)
            pokemon_list = data.get("items", [])

            # Client-side filtering for types
            if st.session_state.selected_types:
                pokemon_list = [
                    p for p in pokemon_list 
                    if any(t.get("type_", {}).get("name") in st.session_state.selected_types for t in p.get("types", []))
                ]
                total_count = len(pokemon_list)

            # Render Grid
            if not pokemon_list:
                st.warning("검색 결과가 없습니다.")
            else:
                grid_html = '<div class="pokemon-grid">'
                for p in pokemon_list:
                    p_types = [(t["type_"]["name"], TYPE_MAP.get(t["type_"]["name"], "normal")) for t in p.get("types", [])]
                    img_url = p.get("image_url") or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png"
                    grid_html += render_pokemon_card(p["id"], p["name"], img_url, p_types)
                grid_html += '</div>'
                
                st.markdown(grid_html, unsafe_allow_html=True)

                # Load More Button
                if total_count > st.session_state.pokemon_limit:
                    st.markdown('<div class="load-more-container">', unsafe_allow_html=True)
                    st.button("더 보기", on_click=load_more)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error(f"백엔드 서버와 통신할 수 없습니다. (Status: {response.status_code})")
            
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

