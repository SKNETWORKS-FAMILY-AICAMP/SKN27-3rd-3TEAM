import json
import os
import urllib.parse
import sys
import requests
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
frontend_dir = os.path.join(root_dir, "frontend")
if root_dir not in sys.path:
    sys.path.append(root_dir)
if frontend_dir not in sys.path:
    sys.path.append(frontend_dir)

from utils.ui import inject_common_ui
from pokedex.styles import get_pokedex_styles, render_pokemon_card

BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"
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


@st.cache_data(show_spinner=False)
def fetch_abilities():
    try:
        resp = requests.get(f"{BACKEND_URL}{API_V1_STR}/abilities")
        if resp.status_code == 200:
            return ["전체"] + sorted(resp.json())
    except:
        pass
    return ["전체"]


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
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)
st.write(get_pokedex_styles(), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Session state defaults ───────────────────────────────────
for key, default in [
    ("pokemon_limit", 50),
    ("search_query", ""),
    ("selected_types", []),
    ("region_filter", "전체"),
    ("dex_start", 1),
    ("dex_end", 1025),
    ("ability_filter", "전체"),
    ("abilities_list", ["전체"]),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.abilities_list == ["전체"]:
    st.session_state.abilities_list = fetch_abilities()


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
    st.session_state.dex_end = 1025
    st.session_state.dex_range_slider = (1, 1025)
    st.session_state.ability_filter = "전체"


def load_more():
    st.session_state.pokemon_limit += 50


REGION_RANGES = {
    "전체": (1, 1025),
    "관동": (1, 151),
    "성도": (152, 251),
    "호연": (252, 386),
    "신오": (387, 493),
    "하나": (494, 649),
    "칼로스": (650, 721),
    "알로라": (722, 809),
    "가라르": (810, 905),
    "팔데아": (906, 1025),
}

def select_region(region):
    """지방 버튼 클릭 시 호출되는 콜백"""
    st.session_state.region_filter = region
    start, end = REGION_RANGES.get(region, (1, 1025))
    st.session_state.dex_start = start
    st.session_state.dex_end = end
    st.session_state.dex_range_slider = (start, end)


def handle_search():
    """검색 및 필터 적용 로직을 한 곳에서 처리"""
    st.session_state.search_query = st.session_state.search_input

    if "ability_sel" in st.session_state:
        st.session_state.ability_filter = st.session_state.ability_sel

    # 슬라이더 현재값을 필터에 반영 (검색 버튼 클릭 시에만)
    if "dex_range_slider" in st.session_state:
        st.session_state.dex_start = st.session_state.dex_range_slider[0]
        st.session_state.dex_end = st.session_state.dex_range_slider[1]


with st.container(border=True):
    st.markdown('<div class="dex-search-card"></div>', unsafe_allow_html=True)
    st.markdown('<div class="dex-top-bg-marker"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="dex-page-title">
        <img src="https://pokemonkorea.co.kr/img/_con.ico" class="dex-title-icon">
        <span>포켓몬 도감</span>
    </div>
    """, unsafe_allow_html=True)
    # ── Search bar & Slider ──────────────────────────────────────
    sc1, sc2 = st.columns([1, 1])
    with sc1:
        search_val = st.text_input(
            "검색",
            value=st.session_state.search_query,
            placeholder="포켓몬 이름 또는 설명, 특성 키워드를 입력하세요.",
            key="search_input",
            on_change=handle_search,
        )
    with sc2:
        st.slider(
            "도감번호",
            min_value=1,
            max_value=1025,
            value=(st.session_state.dex_start, st.session_state.dex_end),
            key="dex_range_slider"
        )
    # ── Left / Right filter columns ──────────────────────────────
    left_col, right_col = st.columns([1, 1.7])

    with left_col:
        ability_idx = 0
        if st.session_state.ability_filter in st.session_state.abilities_list:
            ability_idx = st.session_state.abilities_list.index(st.session_state.ability_filter)
        st.selectbox(
            "특성", st.session_state.abilities_list, index=ability_idx, key="ability_sel"
        )

        st.markdown('<div class="dex-region-label">지방</div>', unsafe_allow_html=True)
        for region_row in [REGIONS[:5], REGIONS[5:]]:
            rcols = st.columns(len(region_row))
            for rcol, region in zip(rcols, region_row):
                with rcol:
                    is_sel = region == st.session_state.region_filter
                    st.markdown(
                        f'<div class="region-btn-box {"region-sel" if is_sel else ""}">{region}</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "", 
                        key=f"region_btn_{region}", 
                        use_container_width=True,
                        on_click=select_region,
                        args=(region,)
                    ):
                        pass

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
                        f'<div class="type-icon-box type-bg-{en.lower()} {sel_cls}">'
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
        st.button("초기화", key="btn_reset", use_container_width=True, on_click=do_reset)
        st.markdown("</div>", unsafe_allow_html=True)

# ── Pokemon grid ─────────────────────────────────────────────
try:
    params = {
        "skip": 0,
        "limit": st.session_state.pokemon_limit,
        "search": st.session_state.search_query or None,
        "ability": st.session_state.ability_filter if st.session_state.ability_filter != "전체" else None,
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
            # 버튼 노출 여부를 결정할 실제 전체 개수 (필터링된 결과의 전체 개수)
            # 여기서는 API가 반환한 'total'을 우선 사용하거나, 타입 필터 등이 적용된 경우 리스트 길이를 사용
            if not st.session_state.selected_types:
                display_total = data.get("total", 0)
            else:
                # 타입 필터는 클라이언트 사이드에서 하므로 전체 리스트(limit 없이)를 가져와야 정확하지만, 
                # 현재 구조상 API의 total을 믿거나 더 큰 값을 잡아야 버튼이 나옴.
                # 일단 넉넉하게 잡아서 버튼이 나오게 함.
                display_total = 1025 

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

            if display_total > st.session_state.pokemon_limit:
                # 버튼을 확실하게 숨기기 위한 마커와 스타일
                st.markdown("""
                    <style>
                        /* 마커 바로 다음에 오는 스트림릿 버튼 감추기 */
                        .load-more-marker + div[data-testid="stButton"] {
                            display: none !important;
                        }
                        /* 혹시 모르니 투명도와 크기까지 조절 */
                        .load-more-marker + div[data-testid="stButton"] button {
                            opacity: 0 !important;
                            height: 0 !important;
                            padding: 0 !important;
                            margin: 0 !important;
                            pointer-events: none !important;
                        }
                        
                        .infinite-loader {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            padding: 40px 0;
                            gap: 10px;
                            color: #888;
                            font-family: 'Inter', sans-serif;
                        }
                        .pokeball-loader {
                            width: 40px;
                            height: 40px;
                            border: 3px solid #333;
                            border-radius: 50%;
                            position: relative;
                            background: linear-gradient(to bottom, #EE1515 50%, white 50%);
                            animation: spin 1s linear infinite;
                        }
                        .pokeball-loader::after {
                            content: '';
                            position: absolute;
                            width: 40px;
                            height: 3px;
                            background: #333;
                            top: 50%;
                            transform: translateY(-50%);
                        }
                        .pokeball-loader::before {
                            content: '';
                            position: absolute;
                            width: 10px;
                            height: 10px;
                            background: white;
                            border: 3px solid #333;
                            border-radius: 50%;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            z-index: 10;
                        }
                        @keyframes spin {
                            from { transform: rotate(0deg); }
                            to { transform: rotate(360deg); }
                        }
                    </style>
                    <div class="load-more-marker"></div>
                    <div class="infinite-loader">
                        <div class="pokeball-loader"></div>
                        <span>포켓몬을 더 불러오고 있어요...</span>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("더 보기", key="btn_load_more", on_click=load_more):
                    pass

                # 무한 스크롤 스크립트: 숨겨진 버튼을 자동으로 클릭
                st.components.v1.html("""
                    <script>
                        function findAndClick() {
                            const buttons = window.parent.document.querySelectorAll('button');
                            for (const btn of buttons) {
                                if (btn.textContent.includes("더 보기")) {
                                    // 클릭 전에 한 번 더 숨김 확인 (보장용)
                                    btn.parentElement.style.display = 'none';
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }

                        const observer = new IntersectionObserver((entries) => {
                            entries.forEach(entry => {
                                if (entry.isIntersecting) {
                                    findAndClick();
                                }
                            });
                        }, { threshold: 0.1 });

                        const interval = setInterval(() => {
                            const marker = window.parent.document.querySelector('.load-more-marker');
                            if (marker) {
                                observer.observe(marker);
                                clearInterval(interval);
                            }
                        }, 500);
                    </script>
                """, height=0)
    else:
        st.error(f"백엔드 서버와 통신할 수 없습니다. (Status: {response.status_code})")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
