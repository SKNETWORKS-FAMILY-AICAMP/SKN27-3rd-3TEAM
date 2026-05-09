import os
import sys
from html import escape
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from neo4j import GraphDatabase


# utils.ui를 import하기 위한 경로 설정입니다.
# 기존 페이지들이 사용하는 공통 헤더/스타일을 그대로 사용하기 위해 유지합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui


# 이 페이지의 목적:
# - 사용자가 포켓몬 5마리를 선택합니다.
# - 선택한 포켓몬 ID를 백엔드 팀 빌더 API로 전달합니다.
# - Neo4j 그래프 DB 기반 분석 결과와 추천 결과를 화면에 보여줍니다.


# BACKEND_API_URL:
# - Docker 안의 frontend 컨테이너에서 실행되면 http://backend:8000 을 사용합니다.
# - 로컬에서 직접 Streamlit을 실행하면 http://localhost:8080 을 fallback으로 사용합니다.
BACKEND_API_URL = os.getenv("BACKEND_API_URL") or os.getenv("BACKEND_URL") or "http://backend:8000"
LOCAL_BACKEND_API_URL = "http://localhost:8080"

# Neo4j 접속 정보:
# - 포켓몬 목록 API가 PostgreSQL 컬럼 문제로 실패할 때, 이 페이지 안에서만 Neo4j를 읽기 위한 값입니다.
# - Docker 안에서는 bolt://neo4j:7687 이 맞고, 로컬 직접 실행에서는 .env의 bolt://localhost:7687 이 맞습니다.
GRAPH_DB_URI = os.getenv("GRAPH_DB_URI", "bolt://localhost:7687")
GRAPH_DB_USER = os.getenv("GRAPH_DB_USER", "neo4j")
GRAPH_DB_PASSWORD = os.getenv("GRAPH_DB_PASSWORD", "")

# REQUIRED_TEAM_SIZE:
# - 현재 팀 추천 API는 5마리를 선택한 뒤 1마리를 추천하는 흐름이므로 5로 고정합니다.
REQUIRED_TEAM_SIZE = 5


st.set_page_config(
    page_title="Team Builder - Pokemon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
)

# 공통 UI:
# - 기존 프로젝트의 헤더, 메뉴, 전역 스타일을 그대로 사용합니다.
inject_common_ui(spacer=True)


def request_json(method: str, path: str, **kwargs: Any) -> Any:
    """백엔드 API를 호출하고 JSON 응답을 반환하기 위한 함수입니다."""

    # urls:
    # - 첫 번째 주소는 현재 실행 환경의 기본 백엔드 주소입니다.
    # - 두 번째 주소는 Docker 밖에서 실행할 때를 대비한 로컬 fallback 주소입니다.
    urls = [BACKEND_API_URL.rstrip("/"), LOCAL_BACKEND_API_URL]
    last_error: Optional[Exception] = None

    for base_url in urls:
        try:
            # response:
            # - method 값에 따라 GET/POST 요청을 모두 처리합니다.
            # - timeout은 백엔드 연결이 오래 멈춰있는 상황을 막기 위한 안전장치입니다.
            response = requests.request(method, f"{base_url}{path}", timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            # HTTPError:
            # - 서버가 500처럼 "응답은 했지만 내부 오류"를 준 경우입니다.
            # - 이때는 다른 주소로 fallback해도 같은 API 문제가 반복될 가능성이 높아서 바로 알려줍니다.
            raise RuntimeError(f"백엔드 API 응답 오류: {exc}") from exc
        except requests.RequestException as exc:
            # last_error:
            # - 모든 주소가 실패했을 때 마지막 오류를 사용자에게 보여주기 위해 저장합니다.
            last_error = exc

    raise RuntimeError(f"백엔드 API 호출 실패: {last_error}")


def get_generation_by_pokemon_id(pokemon_id: int) -> Optional[int]:
    """전국도감 번호를 기준으로 대략적인 세대를 계산하는 함수입니다."""

    # generation_ranges:
    # - 포켓몬 목록 API가 실패했을 때도 세대 필터를 어느 정도 사용할 수 있도록 둔 범위입니다.
    generation_ranges = [
        (1, 151, 1),
        (152, 251, 2),
        (252, 386, 3),
        (387, 493, 4),
        (494, 649, 5),
        (650, 721, 6),
        (722, 809, 7),
        (810, 905, 8),
        (906, 1025, 9),
    ]

    for start_id, end_id, generation in generation_ranges:
        if start_id <= pokemon_id <= end_id:
            return generation
    return None


def build_fallback_pokemon_list() -> List[Dict[str, Any]]:
    """포켓몬 목록 API가 실패했을 때 사용할 임시 선택 목록을 만드는 함수입니다."""

    # fallback_list:
    # - backend의 PostgreSQL 목록 API가 깨져도 팀 추천/분석 API는 테스트할 수 있어야 합니다.
    # - 이름은 분석 API 결과에서 다시 한국어 이름으로 확인할 수 있으므로 여기서는 번호 중심으로 보여줍니다.
    fallback_list: List[Dict[str, Any]] = []
    for pokemon_id in range(1, 1026):
        fallback_list.append(
            {
                "pokemon_id": pokemon_id,
                "name": f"Pokemon {pokemon_id}",
                "image_url": (
                    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                    f"sprites/pokemon/other/official-artwork/{pokemon_id}.png"
                ),
                "generation": get_generation_by_pokemon_id(pokemon_id),
                "base_total": None,
                "types": [],
            }
        )

    return fallback_list


def load_pokemon_list_from_graph() -> List[Dict[str, Any]]:
    """Neo4j에서 포켓몬 이름, 이미지, 타입을 직접 읽어오는 함수입니다."""

    # query:
    # - Pokemon 노드를 기준으로 Type, Species를 함께 가져옵니다.
    # - 기존 PostgreSQL 목록 API가 실패해도 그래프 DB에 적재된 한국어 이름과 타입을 사용할 수 있습니다.
    query = """
    MATCH (p:Pokemon)
    OPTIONAL MATCH (p)-[:HAS_TYPE]->(t:Type)
    OPTIONAL MATCH (p)-[:IS_SPECIES]->(s:Species)
    RETURN p.pokemon_id AS pokemon_id,
           p.name AS name,
           p.image_url AS image_url,
           s.generation AS generation,
           p.base_total AS base_total,
           collect(DISTINCT t.name) AS types
    ORDER BY pokemon_id
    """

    # candidate_uris:
    # - frontend 컨테이너에서는 .env의 localhost가 자기 자신을 의미해서 실패할 수 있습니다.
    # - 그래서 Docker 서비스명 neo4j 주소를 두 번째 후보로 둡니다.
    candidate_uris = [GRAPH_DB_URI, "bolt://neo4j:7687", "bolt://localhost:7687"]
    last_error: Optional[Exception] = None

    for uri in dict.fromkeys(candidate_uris):
        try:
            # driver:
            # - Neo4j와 연결하기 위한 공식 Python 드라이버 객체입니다.
            driver = GraphDatabase.driver(uri, auth=(GRAPH_DB_USER, GRAPH_DB_PASSWORD))
            with driver.session() as session:
                records = session.run(query).data()
            driver.close()
            break
        except Exception as exc:
            last_error = exc
    else:
        raise RuntimeError(f"Neo4j 포켓몬 목록 조회 실패: {last_error}")

    pokemon_list: List[Dict[str, Any]] = []
    for record in records:
        # pokemon_id:
        # - 화면 선택과 팀 추천 API 요청에 그대로 사용하는 ID입니다.
        pokemon_id = record.get("pokemon_id")
        if pokemon_id is None:
            continue

        pokemon_list.append(
            {
                "pokemon_id": int(pokemon_id),
                "name": record.get("name") or f"Pokemon {pokemon_id}",
                "image_url": record.get("image_url") or "",
                "generation": record.get("generation") or get_generation_by_pokemon_id(int(pokemon_id)),
                "base_total": record.get("base_total"),
                "types": [type_name for type_name in record.get("types", []) if type_name],
            }
        )

    return pokemon_list


def normalize_pokemon_list(raw_data: Any) -> List[Dict[str, Any]]:
    """백엔드 응답을 화면에서 쓰기 좋은 포켓몬 목록 형태로 정리하는 함수입니다."""

    # records:
    # - 백엔드가 리스트를 바로 주면 그대로 사용합니다.
    # - dict 안에 data/results/items 등이 있으면 해당 리스트를 꺼냅니다.
    records: List[Dict[str, Any]] = []
    if isinstance(raw_data, list):
        records = raw_data
    elif isinstance(raw_data, dict):
        for key in ("results", "data", "items", "pokemon", "pokemons"):
            if isinstance(raw_data.get(key), list):
                records = raw_data[key]
                break

    normalized: List[Dict[str, Any]] = []
    for item in records:
        # pokemon_id:
        # - 그래프 DB와 팀 추천 API에서 사용하는 핵심 식별자입니다.
        pokemon_id = item.get("pokemon_id") or item.get("id")
        if pokemon_id is None:
            continue

        # raw_types:
        # - 타입 데이터가 문자열 리스트 또는 dict 리스트로 올 수 있어서 둘 다 처리합니다.
        raw_types = item.get("types") or []
        type_names = []
        for type_item in raw_types:
            if isinstance(type_item, dict):
                type_names.append(type_item.get("type_name") or type_item.get("name"))
            else:
                type_names.append(str(type_item))

        normalized.append(
            {
                "pokemon_id": int(pokemon_id),
                "name": item.get("name") or item.get("korean_name") or f"Pokemon {pokemon_id}",
                "image_url": item.get("image_url") or item.get("sprite_url") or "",
                "generation": item.get("generation") or item.get("generation_id"),
                "base_total": item.get("base_total"),
                "types": [name for name in type_names if name],
            }
        )

    return normalized


@st.cache_data(ttl=300)
def load_pokemon_list() -> List[Dict[str, Any]]:
    """포켓몬 선택 화면에 보여줄 전체 포켓몬 목록을 백엔드에서 가져오는 함수입니다."""

    try:
        # raw_data:
        # - 기존 포켓몬 목록 API를 사용합니다.
        # - 응답 구조 차이는 normalize_pokemon_list에서 흡수합니다.
        raw_data = request_json("GET", "/api/v1/pokemon/")
        return normalize_pokemon_list(raw_data)
    except RuntimeError:
        try:
            # graph_fallback:
            # - 기존 포켓몬 목록 API가 실패하면 Neo4j에서 한국어 이름과 타입을 가져옵니다.
            return load_pokemon_list_from_graph()
        except RuntimeError:
            pass

        # final_fallback:
        # - 현재 PostgreSQL pokemon 테이블과 backend 모델의 컬럼이 맞지 않으면 목록 API가 500을 냅니다.
        # - Neo4j 조회까지 실패한 경우에만 최후의 임시 번호 목록으로 대체합니다.
        return build_fallback_pokemon_list()


def find_selected_pokemon(
    pokemon_list: List[Dict[str, Any]], selected_ids: List[int]
) -> List[Dict[str, Any]]:
    """선택된 ID 목록을 실제 포켓몬 정보 목록으로 바꾸는 함수입니다."""

    # pokemon_by_id:
    # - 선택 슬롯을 빠르게 그리기 위해 pokemon_id를 key로 하는 dict를 만듭니다.
    pokemon_by_id = {pokemon["pokemon_id"]: pokemon for pokemon in pokemon_list}
    return [pokemon_by_id[pokemon_id] for pokemon_id in selected_ids if pokemon_id in pokemon_by_id]


def toggle_pokemon(pokemon_id: int) -> None:
    """포켓몬 카드를 클릭했을 때 선택 또는 해제를 처리하는 함수입니다."""

    # selected_ids:
    # - Streamlit rerun 후에도 선택 상태를 유지하기 위해 session_state에 저장합니다.
    selected_ids: List[int] = st.session_state.selected_pokemon_ids

    if pokemon_id in selected_ids:
        selected_ids.remove(pokemon_id)
        return

    if len(selected_ids) >= REQUIRED_TEAM_SIZE:
        st.warning("포켓몬은 5마리까지만 선택할 수 있어요.")
        return

    selected_ids.append(pokemon_id)


def render_selected_slots(selected_pokemon: List[Dict[str, Any]]) -> None:
    """상단에 현재 선택한 5마리 슬롯을 보여주는 함수입니다."""

    st.markdown(
        f"<p class='selected-count'>현재 선택: {len(selected_pokemon)} / {REQUIRED_TEAM_SIZE}</p>",
        unsafe_allow_html=True,
    )

    # columns:
    # - 선택 슬롯 5개를 가로로 고정해서 현재 팀 구성을 바로 확인할 수 있게 합니다.
    columns = st.columns(REQUIRED_TEAM_SIZE)
    for index, column in enumerate(columns):
        with column:
            if index < len(selected_pokemon):
                pokemon = selected_pokemon[index]
                # slot_html:
                # - st.image를 그대로 쓰면 이미지가 너무 크게 렌더링될 수 있어서 HTML img로 크기를 고정합니다.
                slot_html = f"""
                <div class="selected-slot">
                    <img class="selected-slot-image" src="{escape(pokemon["image_url"])}" alt="{escape(pokemon["name"])}">
                    <div class="selected-slot-name">{escape(pokemon["name"])}</div>
                </div>
                """
                st.markdown(slot_html, unsafe_allow_html=True)
            else:
                st.markdown(
                    """
                    <div class="empty-slot">
                        선택 대기
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_pokemon_card(pokemon: Dict[str, Any]) -> None:
    """포켓몬 하나를 선택 가능한 카드 형태로 보여주는 함수입니다."""

    # is_selected:
    # - 선택된 포켓몬이면 버튼 문구와 카드 테두리를 다르게 보여주기 위한 값입니다.
    is_selected = pokemon["pokemon_id"] in st.session_state.selected_pokemon_ids
    card_class = "pokemon-card selected-card" if is_selected else "pokemon-card"

    # type_badges:
    # - 이미지와 버튼 사이에 보여줄 타입 정보입니다.
    # - 현재 fallback 목록에는 타입이 없을 수 있어서 안내 문구를 대신 보여줍니다.
    if pokemon["types"]:
        type_badges = "".join(
            f"<span class='type-badge'>{escape(type_name)}</span>" for type_name in pokemon["types"]
        )
    else:
        type_badges = "<span class='type-placeholder'>타입 분석 후 확인</span>"

    # image_html:
    # - 포켓몬 이미지 크기를 카드 안에서 일정하게 유지하기 위한 HTML입니다.
    if pokemon["image_url"]:
        image_html = (
            f"<img class='pokemon-card-image' src='{escape(pokemon['image_url'])}' "
            f"alt='{escape(pokemon['name'])}'>"
        )
    else:
        image_html = "<div class='missing-image'>No Image</div>"

    # card_html:
    # - 이전처럼 div를 따로 열고 st.image를 넣으면 Streamlit에서 빈 박스가 생길 수 있습니다.
    # - 그래서 카드 본문은 하나의 HTML 덩어리로 렌더링합니다.
    card_html = f"""
    <div class="{card_class}">
        <div class="pokemon-image-wrap">{image_html}</div>
        <div class="pokemon-card-title">{escape(pokemon["name"])}</div>
        <div class="pokemon-type-row">{type_badges}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # button_label:
    # - 이미 선택된 포켓몬이면 해제, 아니면 선택으로 보여줍니다.
    button_label = "해제" if is_selected else "선택"
    st.button(
        button_label,
        key=f"toggle_{pokemon['pokemon_id']}",
        on_click=toggle_pokemon,
        args=(pokemon["pokemon_id"],),
        use_container_width=True,
    )


def render_analysis_result(result: Dict[str, Any]) -> None:
    """팀 분석 API 결과를 사용자가 읽기 좋게 보여주는 함수입니다."""

    st.subheader("포켓몬 덱 분석")

    selected = result.get("selected_pokemon", [])
    if selected:
        st.markdown("**선택한 포켓몬**")
        for pokemon in selected:
            type_text = ", ".join(type_item["type_name"] for type_item in pokemon.get("types", []))
            st.write(f"- #{pokemon['pokemon_id']:04d} {pokemon['name']} | 타입: {type_text}")

    weaknesses = result.get("weaknesses", [])
    resistances = result.get("resistances", [])
    move_coverage = result.get("move_type_coverage", [])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**주의할 약점 타입**")
        if weaknesses:
            for item in weaknesses[:8]:
                st.write(f"- {item['type_name']}: {item['score']}")
        else:
            st.caption("큰 약점 타입이 아직 계산되지 않았어요.")

    with col2:
        st.markdown("**방어가 좋은 타입**")
        if resistances:
            for item in resistances[:8]:
                st.write(f"- {item['type_name']}: {item['score']}")
        else:
            st.caption("저항 타입 정보가 아직 부족해요.")

    with col3:
        st.markdown("**기술 타입 커버리지**")
        if move_coverage:
            for item in move_coverage[:8]:
                st.write(f"- {item['type_name']}: {item['move_count']}개")
        else:
            st.caption("기술 타입 정보가 아직 부족해요.")


def render_recommendation_result(result: Dict[str, Any]) -> None:
    """추천 API 결과를 1~3순위 카드로 보여주는 함수입니다."""

    st.subheader("포켓몬 추천")

    recommendations = result.get("recommendations", [])
    if not recommendations:
        st.info("추천 결과가 아직 없어요.")
        return

    columns = st.columns(min(len(recommendations), 3))
    for index, pokemon in enumerate(recommendations[:3]):
        with columns[index]:
            st.markdown(f"### {pokemon.get('rank', index + 1)}순위")
            if pokemon.get("image_url"):
                st.image(pokemon["image_url"], use_container_width=True)
            st.markdown(f"**#{pokemon['pokemon_id']:04d} {pokemon['name']}**")
            st.caption(f"추천 점수: {pokemon.get('score')}")

            # reasons:
            # - 백엔드가 계산한 추천 근거입니다.
            # - 나중에 RAG를 붙이면 이 근거를 자연어 설명 재료로 사용할 수 있습니다.
            reasons = pokemon.get("reasons") or []
            for reason in reasons:
                st.write(f"- {reason}")


def apply_page_style() -> None:
    """팀 빌더 페이지 전용 CSS를 적용하는 함수입니다."""

    st.markdown(
        """
        <style>
        .main-title {
            text-align: center;
            font-size: 56px;
            font-weight: 900;
            letter-spacing: -2px;
            margin-top: 4px;
        }
        .sub-title {
            text-align: center;
            font-size: 24px;
            margin-bottom: 24px;
        }
        .selected-count {
            text-align: center;
            color: #2563eb;
            font-weight: 800;
            margin-top: 18px;
        }
        .empty-slot {
            height: 138px;
            border: 2px dashed #a9b5c8;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #8b95a7;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.72);
        }
        .selected-slot {
            height: 138px;
            border: 1px solid #c9d3e2;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.84);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 18px rgba(30, 41, 59, 0.08);
            overflow: hidden;
        }
        .selected-slot-image {
            width: 96px;
            height: 92px;
            object-fit: contain;
        }
        .selected-slot-name {
            max-width: 100%;
            padding: 0 8px;
            font-size: 13px;
            font-weight: 800;
            color: #1f2937;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pokemon-card {
            min-height: 210px;
            padding: 10px;
            border: 1px solid #c9d3e2;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.86);
            box-shadow: 0 8px 18px rgba(30, 41, 59, 0.08);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            gap: 6px;
            margin-bottom: 8px;
            overflow: hidden;
        }
        .selected-card {
            border: 3px solid #2f80ed;
            box-shadow: 0 0 0 4px rgba(47, 128, 237, 0.16);
        }
        .pokemon-image-wrap {
            width: 100%;
            height: 118px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(180deg, #f7fbff 0%, #edf4ff 100%);
            border-radius: 12px;
        }
        .pokemon-card-image {
            width: 118px;
            height: 112px;
            object-fit: contain;
        }
        .pokemon-card-title {
            width: 100%;
            text-align: center;
            font-size: 14px;
            font-weight: 900;
            color: #111827;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pokemon-type-row {
            min-height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            flex-wrap: wrap;
        }
        .type-badge {
            padding: 3px 8px;
            border-radius: 999px;
            background: #e0f2fe;
            color: #075985;
            font-size: 12px;
            font-weight: 800;
            border: 1px solid #bae6fd;
        }
        .type-placeholder {
            color: #8b95a7;
            font-size: 12px;
            font-weight: 700;
        }
        .missing-image {
            width: 100%;
            height: 112px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #9aa4b2;
            background: #eef3f8;
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show() -> None:
    """Streamlit 팀 빌더 페이지를 실행하는 메인 함수입니다."""

    apply_page_style()

    # selected_pokemon_ids:
    # - 페이지가 다시 그려져도 선택한 포켓몬 ID를 유지하기 위한 상태값입니다.
    if "selected_pokemon_ids" not in st.session_state:
        st.session_state.selected_pokemon_ids = []

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    if "recommendation_result" not in st.session_state:
        st.session_state.recommendation_result = None

    st.markdown("<div class='main-title'>포켓몬스터 선택</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='sub-title'>({REQUIRED_TEAM_SIZE}마리를 선택해야합니다.)</div>",
        unsafe_allow_html=True,
    )

    try:
        pokemon_list = load_pokemon_list()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    selected_pokemon = find_selected_pokemon(pokemon_list, st.session_state.selected_pokemon_ids)
    render_selected_slots(selected_pokemon)

    generation_values = sorted(
        {pokemon["generation"] for pokemon in pokemon_list if pokemon.get("generation") is not None}
    )

    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        # selected_generation:
        # - 특정 세대만 보고 싶을 때 사용하는 필터값입니다.
        selected_generation = st.selectbox("세대", ["전체"] + generation_values)
    with search_col:
        # keyword:
        # - 포켓몬 이름 또는 ID로 빠르게 찾기 위한 검색어입니다.
        keyword = st.text_input("검색", placeholder="포켓몬 이름 또는 번호 검색")

    filtered_pokemon = pokemon_list
    if selected_generation != "전체":
        filtered_pokemon = [
            pokemon for pokemon in filtered_pokemon if pokemon.get("generation") == selected_generation
        ]

    if keyword:
        filtered_pokemon = [
            pokemon
            for pokemon in filtered_pokemon
            if keyword.lower() in pokemon["name"].lower()
            or keyword.strip() == str(pokemon["pokemon_id"])
        ]

    st.divider()

    # 스크롤 영역:
    # - 포켓몬 카드가 많기 때문에 높이를 고정한 컨테이너 안에서 위아래로 이동하게 합니다.
    with st.container(height=560, border=True):
        grid_columns = st.columns(6)
        for index, pokemon in enumerate(filtered_pokemon):
            with grid_columns[index % 6]:
                render_pokemon_card(pokemon)

    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])
    with action_col1:
        if st.button("선택 초기화", use_container_width=True):
            st.session_state.selected_pokemon_ids = []
            st.session_state.analysis_result = None
            st.session_state.recommendation_result = None
            st.rerun()

    can_request = len(st.session_state.selected_pokemon_ids) == REQUIRED_TEAM_SIZE
    with action_col2:
        if st.button("덱 분석", disabled=not can_request, use_container_width=True):
            payload = {"pokemon_ids": st.session_state.selected_pokemon_ids}
            st.session_state.analysis_result = request_json(
                "POST", "/api/v1/team-builder/analyze", json=payload
            )

    with action_col3:
        if st.button("추천 받기", disabled=not can_request, use_container_width=True):
            payload = {"pokemon_ids": st.session_state.selected_pokemon_ids, "limit": 3}
            st.session_state.recommendation_result = request_json(
                "POST", "/api/v1/team-builder/recommend", json=payload
            )

    if st.session_state.analysis_result:
        render_analysis_result(st.session_state.analysis_result)

    if st.session_state.recommendation_result:
        render_recommendation_result(st.session_state.recommendation_result)


if __name__ == "__main__":
    show()
