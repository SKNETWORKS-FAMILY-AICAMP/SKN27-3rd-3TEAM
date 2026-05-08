import json
import os
import sys
from pathlib import Path

import requests
import streamlit as st

# pages 폴더에서 실행되므로 frontend/utils 를 import 할 수 있게 경로를 추가합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui


# 이 상수는 사용자가 추천을 받기 위해 반드시 선택해야 하는 포켓몬 수를 의미합니다.
REQUIRED_TEAM_SIZE = 5

# 이 경로는 프론트엔드 파일 기준으로 프로젝트 루트의 processed JSON 폴더를 가리킵니다.
PROCESSED_DATA_DIR = (
    Path(__file__).resolve().parents[2] / "database" / "common" / "data" / "processed"
)

# BACKEND_URL은 Docker에서는 backend 서비스 주소, 로컬에서는 localhost 백엔드 주소를 의미합니다.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")


@st.cache_data
def load_local_pokedex_data():
    """백엔드가 꺼져 있을 때 로컬 JSON으로 포켓몬 선택 데이터를 불러오기 위해 작성한 함수입니다."""

    # pokemon.json은 카드에 표시할 이름, 이미지, 기본 포켓몬 여부를 담고 있습니다.
    with open(PROCESSED_DATA_DIR / "pokemon.json", "r", encoding="utf-8") as file:
        pokemon_rows = json.load(file)

    # species.json은 각 포켓몬이 몇 세대에 등장했는지 판단하기 위해 사용합니다.
    with open(PROCESSED_DATA_DIR / "species.json", "r", encoding="utf-8") as file:
        species_rows = json.load(file)

    # pokemon_types.json은 포켓몬 카드에 타입 배지를 보여주기 위해 사용합니다.
    with open(PROCESSED_DATA_DIR / "pokemon_types.json", "r", encoding="utf-8") as file:
        pokemon_type_rows = json.load(file)

    # types.json은 type_id를 사람이 읽을 수 있는 타입 이름으로 바꾸기 위해 사용합니다.
    with open(PROCESSED_DATA_DIR / "types.json", "r", encoding="utf-8") as file:
        type_rows = json.load(file)

    # species_by_pokemon_id는 포켓몬 ID로 세대 정보를 빠르게 찾기 위한 딕셔너리입니다.
    species_by_pokemon_id = {
        row["pokemon_id"]: row for row in species_rows if row.get("pokemon_id")
    }

    # type_name_by_id는 타입 ID를 타입 이름으로 바꾸기 위한 딕셔너리입니다.
    type_name_by_id = {row["id"]: row["name"] for row in type_rows}

    # types_by_pokemon_id는 포켓몬별 타입 목록을 모아두기 위한 딕셔너리입니다.
    types_by_pokemon_id = {}
    for row in pokemon_type_rows:
        pokemon_id = row["pokemon_id"]
        type_name = type_name_by_id.get(row["type_id"], "알 수 없음")
        types_by_pokemon_id.setdefault(pokemon_id, []).append(type_name)

    # cards는 실제 화면에서 반복 출력할 포켓몬 카드 데이터 목록입니다.
    cards = []
    for pokemon in pokemon_rows:
        pokemon_id = pokemon["id"]
        species = species_by_pokemon_id.get(pokemon_id)

        # 추천 선택 단계에서는 메가진화/폼 체인지가 섞이지 않도록 기본 포켓몬만 보여줍니다.
        if not pokemon.get("is_default") or species is None:
            continue

        cards.append(
            {
                "id": pokemon_id,
                "name": pokemon["name"],
                "image_url": pokemon["image_url"],
                "generation": species["generation"],
                "types": types_by_pokemon_id.get(pokemon_id, []),
            }
        )

    return cards


@st.cache_data(ttl=60)
def fetch_pokedex_data_from_api(generation_filter, search_text):
    """백엔드 API에서 포켓몬 카드 목록을 가져오기 위해 작성한 함수입니다."""

    # generation은 "1세대" 같은 화면 값을 API가 이해하는 숫자로 바꾼 값입니다.
    generation = None
    if generation_filter != "전체 세대":
        generation = int(generation_filter.replace("세대", ""))

    # params는 백엔드 포켓몬 목록 API에 전달할 검색/세대/페이지 조건입니다.
    params = {
        "skip": 0,
        "limit": 200,
        "search": search_text.strip() or None,
        "generation": generation,
        "is_default_only": True,
    }

    # None 값은 실제 요청 URL에 붙이지 않기 위해 제거합니다.
    params = {key: value for key, value in params.items() if value is not None}

    # all_cards는 페이지네이션으로 나뉜 포켓몬 목록을 하나로 모으는 리스트입니다.
    all_cards = []

    while True:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/pokemon/",
            params=params,
            timeout=8,
        )
        response.raise_for_status()

        # payload는 백엔드가 반환한 total, skip, limit, items 데이터를 담고 있습니다.
        payload = response.json()

        for pokemon in payload["items"]:
            # types는 백엔드의 중첩 타입 응답을 화면 배지용 문자열 목록으로 바꾼 값입니다.
            types = [
                type_row["type_"]["name"]
                for type_row in pokemon.get("types", [])
                if type_row.get("type_")
            ]

            all_cards.append(
                {
                    "id": pokemon["id"],
                    "name": pokemon["name"],
                    "image_url": pokemon["image_url"],
                    "generation": pokemon.get("generation"),
                    "types": types,
                }
            )

        # 다음 페이지가 없으면 반복 조회를 멈춥니다.
        if params["skip"] + params["limit"] >= payload["total"]:
            break

        # skip은 다음 페이지에서 건너뛸 포켓몬 개수입니다.
        params["skip"] += params["limit"]

    return all_cards


def load_pokedex_data(generation_filter, search_text):
    """백엔드 API를 우선 사용하고 실패하면 로컬 JSON으로 대체하기 위해 작성한 함수입니다."""

    try:
        cards = fetch_pokedex_data_from_api(generation_filter, search_text)
        return cards, "api"
    except requests.RequestException:
        # fallback_cards는 백엔드가 아직 준비되지 않았을 때 화면 확인용으로 사용하는 로컬 데이터입니다.
        fallback_cards = load_local_pokedex_data()
        return get_filtered_pokemon(fallback_cards, generation_filter, search_text), "local"


def initialize_selection_state():
    """선택한 포켓몬 ID 목록을 Streamlit 세션에 준비하기 위해 작성한 함수입니다."""

    # selected_pokemon_ids는 사용자가 현재 선택한 포켓몬 ID들을 저장합니다.
    if "selected_pokemon_ids" not in st.session_state:
        st.session_state.selected_pokemon_ids = []

    # selected_pokemon_cards는 선택된 카드 정보를 필터 변경 후에도 유지하기 위한 딕셔너리입니다.
    if "selected_pokemon_cards" not in st.session_state:
        st.session_state.selected_pokemon_cards = {}


def toggle_pokemon_selection(card):
    """카드를 눌렀을 때 선택/해제를 처리하기 위해 작성한 함수입니다."""

    # pokemon_id는 선택/해제를 판단할 포켓몬의 고유 ID입니다.
    pokemon_id = card["id"]

    # selected_ids는 현재 선택된 포켓몬 ID 목록을 짧게 부르기 위한 변수입니다.
    selected_ids = st.session_state.selected_pokemon_ids

    # 이미 선택된 포켓몬이면 다시 눌렀을 때 선택 해제합니다.
    if pokemon_id in selected_ids:
        selected_ids.remove(pokemon_id)
        st.session_state.selected_pokemon_cards.pop(pokemon_id, None)
        return

    # 아직 5마리를 다 고르지 않았다면 새 포켓몬을 선택 목록에 추가합니다.
    if len(selected_ids) < REQUIRED_TEAM_SIZE:
        selected_ids.append(pokemon_id)
        st.session_state.selected_pokemon_cards[pokemon_id] = card


def get_filtered_pokemon(cards, generation_filter, search_text):
    """세대 필터와 검색어에 맞는 포켓몬만 남기기 위해 작성한 함수입니다."""

    # normalized_search는 대소문자 차이 없이 검색하기 위해 정리한 검색어입니다.
    normalized_search = search_text.strip().lower()

    # filtered_cards는 조건에 맞는 포켓몬 카드만 담는 목록입니다.
    filtered_cards = []
    for card in cards:
        matches_generation = (
            generation_filter == "전체 세대"
            or card["generation"] == int(generation_filter.replace("세대", ""))
        )
        matches_search = normalized_search in card["name"].lower()

        # 세대와 검색어 조건을 모두 만족하는 카드만 화면에 보여줍니다.
        if matches_generation and matches_search:
            filtered_cards.append(card)

    return filtered_cards


def render_pokemon_card(card):
    """포켓몬 한 마리의 이미지 카드와 선택 버튼을 그리기 위해 작성한 함수입니다."""

    # is_selected는 현재 카드가 사용자가 선택한 5마리 안에 들어있는지 의미합니다.
    is_selected = card["id"] in st.session_state.selected_pokemon_ids

    # selected_class는 선택된 카드에 파란 테두리를 입히기 위한 CSS 클래스 이름입니다.
    selected_class = " selected-card" if is_selected else ""

    # type_badges는 포켓몬 타입을 작은 배지 형태로 보여주기 위한 HTML 문자열입니다.
    type_badges = "".join(
        f'<span class="type-badge">{type_name}</span>' for type_name in card["types"]
    )

    # 카드 HTML은 이미지, 이름, 타입을 하나의 사각형 영역으로 묶어서 보여줍니다.
    st.markdown(
        f"""
        <div class="pokemon-card{selected_class}">
            <div class="pokemon-image-box">
                <img src="{card["image_url"]}" alt="{card["name"]}">
            </div>
            <div class="pokemon-name">#{card["id"]:04d} {card["name"]}</div>
            <div class="pokemon-types">{type_badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 카드 아래 버튼은 실제 선택/해제 이벤트를 처리하는 Streamlit 버튼입니다.
    button_label = "선택 해제" if is_selected else "선택"
    if st.button(button_label, key=f"select_pokemon_{card['id']}", use_container_width=True):
        toggle_pokemon_selection(card)
        st.rerun()


def render_selected_team():
    """현재 선택한 5마리를 화면 상단에 요약해서 보여주기 위해 작성한 함수입니다."""

    # selected_cards는 선택 순서대로 포켓몬 정보를 담은 목록입니다.
    selected_cards = [
        st.session_state.selected_pokemon_cards[pokemon_id]
        for pokemon_id in st.session_state.selected_pokemon_ids
        if pokemon_id in st.session_state.selected_pokemon_cards
    ]

    st.markdown('<div class="selected-team-row">', unsafe_allow_html=True)
    selected_columns = st.columns(REQUIRED_TEAM_SIZE)

    for index, column in enumerate(selected_columns):
        with column:
            if index < len(selected_cards):
                card = selected_cards[index]
                st.markdown(
                    f"""
                    <div class="selected-slot filled-slot">
                        <img src="{card["image_url"]}" alt="{card["name"]}">
                        <strong>{card["name"]}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="selected-slot empty-slot">
                        <span>선택 대기</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)


def inject_page_style():
    """첫 번째 이미지의 와이어프레임을 Pokédex 느낌으로 다듬는 CSS를 넣기 위해 작성한 함수입니다."""

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Gowun+Dodum&display=swap');

        .block-container {
            max-width: 1360px !important;
            padding: 118px 28px 36px !important;
        }

        .top-nav {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            transform: none !important;
        }

        .pokedex-hero {
            text-align: center;
            margin-bottom: 20px;
        }

        .pokedex-hero h1 {
            color: #1f2937;
            font-family: 'Black Han Sans', sans-serif;
            font-size: clamp(36px, 4vw, 56px);
            letter-spacing: 2px;
            margin: 0;
        }

        .pokedex-hero p {
            color: #374151;
            font-family: 'Gowun Dodum', sans-serif;
            font-size: clamp(18px, 1.7vw, 25px);
            margin: 8px 0 0;
        }

        div[data-testid="stSelectbox"] > div,
        div[data-testid="stTextInput"] > div {
            border-radius: 0 !important;
            min-height: 54px;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input {
            background: #ffffff !important;
            border: 2px solid #20242c !important;
            border-radius: 0 !important;
            min-height: 54px !important;
            font-size: 18px !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
        }

        .selected-guide {
            color: #2563eb;
            font-weight: 800;
            margin: 12px 0 12px;
            text-align: center;
        }

        .selected-slot {
            align-items: center;
            background: #ffffff;
            border: 2px dashed #9ca3af;
            border-radius: 14px;
            display: flex;
            flex-direction: column;
            height: 116px;
            justify-content: center;
            margin-bottom: 6px;
            overflow: hidden;
            padding: 8px;
            text-align: center;
        }

        .selected-slot img {
            height: 74px;
            object-fit: contain;
            width: 100%;
        }

        .filled-slot {
            border: 3px solid #2f9bff;
            box-shadow: 0 0 0 4px rgba(47, 155, 255, 0.14);
        }

        .empty-slot span {
            color: #9ca3af;
            font-weight: 700;
        }

        .pokemon-card {
            background: #ffffff;
            border: 2px solid #20242c;
            border-radius: 12px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            min-height: 192px;
            padding: 9px;
            transition: all 0.16s ease;
        }

        .pokemon-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.12);
        }

        .selected-card {
            border: 4px solid #2f9bff;
            box-shadow: 0 0 0 5px rgba(47, 155, 255, 0.18), 0 20px 40px rgba(37, 99, 235, 0.16);
        }

        .pokemon-image-box {
            align-items: center;
            background: radial-gradient(circle at top, #ffffff 0%, #eaf3ff 58%, #dbeafe 100%);
            border: 1px solid #d6dee8;
            border-radius: 10px;
            display: flex;
            height: 104px;
            justify-content: center;
            margin-bottom: 8px;
        }

        .pokemon-image-box img {
            height: 94px;
            object-fit: contain;
            width: 100%;
        }

        .pokemon-name {
            color: #111827;
            font-size: 14px;
            font-weight: 900;
            overflow: hidden;
            text-align: center;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .pokemon-types {
            display: flex;
            gap: 6px;
            justify-content: center;
            margin-top: 6px;
            min-height: 24px;
        }

        .type-badge {
            background: #111827;
            border-radius: 999px;
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            padding: 3px 8px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid #20242c;
            border-radius: 18px;
            box-shadow: inset -10px 0 0 rgba(17, 24, 39, 0.08);
        }

        .next-button-note {
            color: #ef4444;
            font-family: 'Gowun Dodum', sans-serif;
            font-size: 18px;
            font-weight: 800;
            margin-top: 12px;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Pokédex Team Selector",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=False)
inject_page_style()
initialize_selection_state()

# selected_count는 현재 사용자가 선택한 포켓몬 수를 의미합니다.
selected_count = len(st.session_state.selected_pokemon_ids)

st.markdown(
    f"""
    <section class="pokedex-hero">
        <h1>포켓몬스터 선택</h1>
        <p>({REQUIRED_TEAM_SIZE}마리를 선택해야합니다.)</p>
    </section>
    """,
    unsafe_allow_html=True,
)

filter_left, filter_right = st.columns([1, 1.1])

with filter_left:
    # generation_filter는 특정 세대 포켓몬만 보고 싶을 때 사용하는 선택값입니다.
    generation_filter = st.selectbox(
        "세대",
        ["전체 세대"] + [f"{generation}세대" for generation in range(1, 10)],
        index=1,
        label_visibility="collapsed",
    )

with filter_right:
    # search_text는 포켓몬 이름으로 목록을 좁히기 위한 검색어입니다.
    search_text = st.text_input(
        "검색",
        placeholder="포켓몬 이름 검색",
        label_visibility="collapsed",
    )

# cards는 화면에서 보여줄 포켓몬 카드 데이터이며, API 실패 시 로컬 JSON을 사용합니다.
cards, data_source = load_pokedex_data(generation_filter, search_text)

if data_source == "local":
    st.warning("백엔드 API에 연결하지 못해 로컬 JSON 데이터로 임시 표시 중입니다.")

st.markdown(
    f'<p class="selected-guide">현재 선택: {selected_count} / {REQUIRED_TEAM_SIZE}</p>',
    unsafe_allow_html=True,
)

render_selected_team()

# 오른쪽 스크롤 느낌을 만들기 위해 높이가 고정된 Streamlit 컨테이너 안에 카드 그리드를 넣습니다.
with st.container(height=570, border=True):
    if not cards:
        st.info("조건에 맞는 포켓몬이 없습니다.")
    else:
        # row_size는 한 줄에 보여줄 포켓몬 카드 개수를 의미합니다.
        row_size = 8
        for start_index in range(0, len(cards), row_size):
            row_cards = cards[start_index : start_index + row_size]
            columns = st.columns(row_size)

            for column, card in zip(columns, row_cards):
                with column:
                    render_pokemon_card(card)

bottom_left, bottom_right = st.columns([4, 1])

with bottom_left:
    if selected_count == REQUIRED_TEAM_SIZE:
        st.success("5마리 선택이 완료되었습니다. 다음 단계에서 이 팀을 분석할 수 있습니다.")
    else:
        st.caption("포켓몬 카드를 선택하면 파란 테두리로 표시됩니다.")

with bottom_right:
    # 다음 버튼은 5마리를 모두 골랐을 때만 분석 단계로 넘어갈 수 있도록 활성화합니다.
    go_next = st.button(
        "다음",
        type="primary",
        use_container_width=True,
        disabled=selected_count != REQUIRED_TEAM_SIZE,
    )

if go_next:
    # selected_team_for_analysis는 다음 분석/추천 화면에서 사용할 선택 팀 ID 목록입니다.
    st.session_state.selected_team_for_analysis = st.session_state.selected_pokemon_ids.copy()
    st.session_state.pokedex_step = "analysis"
    st.info("선택한 5마리를 저장했습니다. 다음 단계에서는 분석 화면과 연결하면 됩니다.")

if selected_count != REQUIRED_TEAM_SIZE:
    st.markdown(
        '<p class="next-button-note">5마리 포켓몬을 선택하면 다음으로 이동할 수 있습니다.</p>',
        unsafe_allow_html=True,
    )
