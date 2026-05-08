import streamlit as st
import sys
import os
import urllib.parse
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
frontend_dir = os.path.join(root_dir, "frontend")
if root_dir not in sys.path:
    sys.path.append(root_dir)
if frontend_dir not in sys.path:
    sys.path.append(frontend_dir)

from utils.ui import inject_common_ui
from pages.style.pokedex_styles import get_pokedex_styles, render_pokemon_card

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_V1_STR = "/api/v1/pokemon"

REGIONS = ["전체", "관동", "성도", "호연", "신오", "하나", "칼로스", "알로라", "가라르", "팔데아"]

TYPE_ORDER = [
    ("노말", "normal"), ("풀", "grass"),   ("불꽃", "fire"),    ("물", "water"),
    ("전기", "electric"), ("벌레", "bug"), ("비행", "flying"),  ("바위", "rock"),
    ("독", "poison"),   ("땅", "ground"),  ("얼음", "ice"),     ("격투", "fighting"),
    ("에스퍼", "psychic"), ("고스트", "ghost"), ("드래곤", "dragon"), ("악", "dark"),
    ("강철", "steel"),  ("페어리", "fairy"),
]

KO_TO_EN = {ko: en for ko, en in TYPE_ORDER}
EN_TO_KO = {en: ko for ko, en in TYPE_ORDER}

_ICON_FILENAME_OVERRIDE = {"얼음": "아이스"}


@st.cache_data
def load_type_icons():
    """SVG를 직접 읽어와서 문자열로 반환 — 직접 HTML에 삽입 가능"""
    # 현재 파일 기준 절대 경로로 아이콘 디렉토리 지정
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_dir = os.path.join(base_path, "img", "type")
    
    icons = {}
    for ko, _ in TYPE_ORDER:
        filename = _ICON_FILENAME_OVERRIDE.get(ko, ko)
        path = os.path.join(icon_dir, f"{filename}.svg")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    svg = f.read()
                icons[ko] = svg
            else:
                icons[ko] = ""
        except Exception:
            icons[ko] = ""
    return icons


st.set_page_config(
    page_title="포켓몬 비공식 도감",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
)

inject_common_ui(spacer=True)
st.write(get_pokedex_styles(), unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)

# ── Session state defaults ───────────────────────────────────
for key, default in [
    ("pokemon_limit", 2000),
    ("search_query", ""),
    ("selected_types", []),
    ("region_filter", "전체"),
    ("dex_start", 1),
    ("dex_end", 2000),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def toggle_type(en):
    lst = st.session_state.selected_types
    if en in lst:
        lst.remove(en)
    else:
        lst.append(en)


def do_reset():
    st.session_state.search_query = ""
    st.session_state.selected_types = []
    st.session_state.region_filter = "전체"
    st.session_state.dex_start = 1
    st.session_state.dex_end = 2000


def load_more():
    st.session_state.pokemon_limit += 20


def handle_search():
    """검색 및 필터 적용 로직을 한 곳에서 처리"""
    # 폼 위젯의 현재 값들을 session_state에 저장
    st.session_state.search_query = st.session_state.search_input
    if "region_sel" in st.session_state:
        st.session_state.region_filter = st.session_state.region_sel
    if "dex_start_input" in st.session_state:
        st.session_state.dex_start = int(st.session_state.dex_start_input)
    if "dex_end_input" in st.session_state:
        st.session_state.dex_end = int(st.session_state.dex_end_input)

with st.container():
    st.markdown('<div class="dex-top-bg-marker"></div>', unsafe_allow_html=True)
    # ── Search bar (full width) ──────────────────────────────────
    search_val = st.text_input(
        "search",
        value=st.session_state.search_query,
        placeholder="포켓몬 이름 또는 설명, 특성 키워드를 입력하세요.",
        label_visibility="collapsed",
        key="search_input",
        on_change=handle_search,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Left / Right filter columns ──────────────────────────────
    left_col, right_col = st.columns([1, 1.7])

    with left_col:
        st.selectbox("특성", ["전체"], key="ability_sel", label_visibility="visible")

        region_idx = REGIONS.index(st.session_state.region_filter)
        region_val = st.selectbox(
            "지방", REGIONS, index=region_idx, key="region_sel", label_visibility="visible"
        )

        st.markdown('<div class="dex-numrange-label">도감번호</div>', unsafe_allow_html=True)
        nc1, nc2, nc3 = st.columns([1, 0.18, 1])
        with nc1:
            dex_start_val = st.number_input(
                "시작", min_value=1, max_value=2000,
                value=st.session_state.dex_start,
                label_visibility="collapsed", key="dex_start_input",
            )
        with nc2:
            st.markdown('<div class="dex-range-sep">-</div>', unsafe_allow_html=True)
        with nc3:
            dex_end_val = st.number_input(
                "끝", min_value=1, max_value=2000,
                value=st.session_state.dex_end,
                label_visibility="collapsed", key="dex_end_input",
            )

    # ── Type icon grid ───────────────────────────────────────────
    type_icons = load_type_icons()

    with right_col:
        st.markdown('<div class="dex-type-label">타입</div>', unsafe_allow_html=True)
        rows = [TYPE_ORDER[:6], TYPE_ORDER[6:12], TYPE_ORDER[12:18]]
        for row in rows:
            cols = st.columns(len(row))
            for col, (ko, en) in zip(cols, row):
                with col:
                    is_sel = en in st.session_state.selected_types
                    sel_cls = "type-sel" if is_sel else ""
                    svg_icon = type_icons.get(ko, "")
                    
                    # SVG가 있으면 지정된 CSS 클래스로 감싸서 출력
                    icon_html = f'<div class="type-svg-wrap">{svg_icon}</div>' if svg_icon else ""
                    
                    st.markdown(
                        f'<div class="type-icon-box {sel_cls}">'
                        f'{icon_html}'
                        f'<span>{ko}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("", key=f"type_{en}", use_container_width=True):
                        toggle_type(en)
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Search / Reset buttons ───────────────────────────────────
    _, bc1, bc2, _ = st.columns([2, 2, 2, 2])
    with bc1:
        st.markdown('<div class="dex-btn-search">', unsafe_allow_html=True)
        if st.button("검색", key="btn_search", use_container_width=True):
            handle_search()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with bc2:
        st.markdown('<div class="dex-btn-reset">', unsafe_allow_html=True)
        if st.button("초기화", key="btn_reset", use_container_width=True):
            do_reset()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ── Pokemon grid ─────────────────────────────────────────────
try:
    params = {
        "skip": 0,
        "limit": st.session_state.pokemon_limit,
        "search": st.session_state.search_query or None,
    }
    response = requests.get(f"{BACKEND_URL}{API_V1_STR}/", params=params)

    if response.status_code == 200:
        data = response.json()
        total_count = data.get("total", 0)
        pokemon_list = data.get("items", [])
        
        # ID range filter (Use species_id for varieties, fall back to id)
        pokemon_list = [
            p for p in pokemon_list
            if st.session_state.dex_start <= (p.get("species_id") or p["id"]) <= st.session_state.dex_end
        ]

        if st.session_state.selected_types:
            selected_ko = {EN_TO_KO[en] for en in st.session_state.selected_types}
            pokemon_list = [
                p for p in pokemon_list
                if any(t.get("type_", {}).get("name") in selected_ko for t in p.get("types", []))
            ]
            total_count = len(pokemon_list)
        else:
            total_count = len(pokemon_list)

        if not pokemon_list:
            st.warning("검색 결과가 없습니다.")
        else:
            grid_html = '<div class="pokemon-grid">'
            for p in pokemon_list:
                p_types_raw = sorted(p.get("types", []), key=lambda x: x.get("slot", 1))
                p_types = [
                    (t["type_"]["name"], KO_TO_EN.get(t["type_"]["name"], "normal"))
                    for t in p_types_raw
                ]
                img_url = (
                    p.get("image_url")
                    or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png"
                )
                grid_html += render_pokemon_card(p["id"], p["name"], img_url, p_types, display_id=p.get("species_id"))
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)

            if total_count > st.session_state.pokemon_limit:
                st.markdown('<div class="load-more-container">', unsafe_allow_html=True)
                st.button("더 보기", on_click=load_more)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error(f"백엔드 서버와 통신할 수 없습니다. (Status: {response.status_code})")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
