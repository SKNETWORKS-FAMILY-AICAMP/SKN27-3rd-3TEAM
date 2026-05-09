import os
import sys
from html import escape
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


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

# REQUIRED_TEAM_SIZE:
# - 현재 팀 추천 API는 5마리를 선택한 뒤 1마리를 추천하는 흐름이므로 5로 고정합니다.
REQUIRED_TEAM_SIZE = 5

# TYPE_BADGE_STYLES:
# - 포켓몬 타입별 배지 색상입니다.
# - Neo4j 데이터가 한국어 타입명으로 내려오므로 한국어를 기본으로 두고,
#   나중에 영문 타입명이 섞여도 깨지지 않도록 영문 키도 함께 넣었습니다.
TYPE_BADGE_STYLES: Dict[str, Dict[str, str]] = {
    "노말": {"bg": "#E5E7EB", "border": "#9CA3AF", "text": "#374151"},
    "Normal": {"bg": "#E5E7EB", "border": "#9CA3AF", "text": "#374151"},
    "불꽃": {"bg": "#F97316", "border": "#EA580C", "text": "#FFFFFF"},
    "Fire": {"bg": "#F97316", "border": "#EA580C", "text": "#FFFFFF"},
    "물": {"bg": "#38BDF8", "border": "#0284C7", "text": "#082F49"},
    "Water": {"bg": "#38BDF8", "border": "#0284C7", "text": "#082F49"},
    "전기": {"bg": "#FACC15", "border": "#CA8A04", "text": "#422006"},
    "Electric": {"bg": "#FACC15", "border": "#CA8A04", "text": "#422006"},
    "풀": {"bg": "#22C55E", "border": "#16A34A", "text": "#FFFFFF"},
    "Grass": {"bg": "#22C55E", "border": "#16A34A", "text": "#FFFFFF"},
    "얼음": {"bg": "#A5F3FC", "border": "#06B6D4", "text": "#164E63"},
    "Ice": {"bg": "#A5F3FC", "border": "#06B6D4", "text": "#164E63"},
    "격투": {"bg": "#DC2626", "border": "#991B1B", "text": "#FFFFFF"},
    "Fighting": {"bg": "#DC2626", "border": "#991B1B", "text": "#FFFFFF"},
    "독": {"bg": "#A855F7", "border": "#7E22CE", "text": "#FFFFFF"},
    "Poison": {"bg": "#A855F7", "border": "#7E22CE", "text": "#FFFFFF"},
    "땅": {"bg": "#D6A85A", "border": "#A16207", "text": "#422006"},
    "Ground": {"bg": "#D6A85A", "border": "#A16207", "text": "#422006"},
    "비행": {"bg": "#93C5FD", "border": "#3B82F6", "text": "#172554"},
    "Flying": {"bg": "#93C5FD", "border": "#3B82F6", "text": "#172554"},
    "에스퍼": {"bg": "#F472B6", "border": "#DB2777", "text": "#FFFFFF"},
    "Psychic": {"bg": "#F472B6", "border": "#DB2777", "text": "#FFFFFF"},
    "벌레": {"bg": "#84CC16", "border": "#4D7C0F", "text": "#1A2E05"},
    "Bug": {"bg": "#84CC16", "border": "#4D7C0F", "text": "#1A2E05"},
    "바위": {"bg": "#A16207", "border": "#713F12", "text": "#FFFFFF"},
    "Rock": {"bg": "#A16207", "border": "#713F12", "text": "#FFFFFF"},
    "고스트": {"bg": "#6D28D9", "border": "#4C1D95", "text": "#FFFFFF"},
    "Ghost": {"bg": "#6D28D9", "border": "#4C1D95", "text": "#FFFFFF"},
    "드래곤": {"bg": "#4338CA", "border": "#312E81", "text": "#FFFFFF"},
    "Dragon": {"bg": "#4338CA", "border": "#312E81", "text": "#FFFFFF"},
    "악": {"bg": "#374151", "border": "#111827", "text": "#FFFFFF"},
    "Dark": {"bg": "#374151", "border": "#111827", "text": "#FFFFFF"},
    "강철": {"bg": "#94A3B8", "border": "#64748B", "text": "#0F172A"},
    "Steel": {"bg": "#94A3B8", "border": "#64748B", "text": "#0F172A"},
    "페어리": {"bg": "#F9A8D4", "border": "#EC4899", "text": "#831843"},
    "Fairy": {"bg": "#F9A8D4", "border": "#EC4899", "text": "#831843"},
}


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
        # graph_list:
        # - 카드에서 한국어 이름과 타입을 바로 보여주기 위해 Neo4j 목록을 우선 사용합니다.
        # - 기존 /api/v1/pokemon/ 응답은 타입이 비어 있을 수 있어서 후순위로 둡니다.
        raw_data = request_json("GET", "/api/v1/team-builder/pokemon-options")
        normalized = normalize_pokemon_list(raw_data)
        if normalized:
            return normalized
    except RuntimeError:
        try:
            # api_fallback:
            # - 팀빌더 전용 목록 API가 실패할 때만 기존 포켓몬 목록 API를 사용합니다.
            raw_data = request_json("GET", "/api/v1/pokemon/")
            normalized = normalize_pokemon_list(raw_data)
            if any(pokemon["types"] for pokemon in normalized):
                return normalized
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
        # 선택 구성이 바뀌면 이전 덱 분석/추천 결과는 더 이상 현재 팀의 결과가 아닙니다.
        st.session_state.analysis_result = None
        st.session_state.recommendation_result = None
        return

    if len(selected_ids) >= REQUIRED_TEAM_SIZE:
        st.warning("포켓몬은 5마리까지만 선택할 수 있어요.")
        return

    selected_ids.append(pokemon_id)
    # 새 포켓몬을 추가한 뒤에도 이전 분석/추천 결과를 지워서 화면 불일치를 막습니다.
    st.session_state.analysis_result = None
    st.session_state.recommendation_result = None


def get_type_badge_style(type_name: str) -> str:
    """타입 이름에 맞는 배지 색상 CSS를 만들어주는 함수입니다."""

    # palette:
    # - 타입명이 색상표에 없을 때도 화면이 깨지지 않도록 기본 회색 배지를 사용합니다.
    palette = TYPE_BADGE_STYLES.get(
        type_name,
        {"bg": "#E5E7EB", "border": "#9CA3AF", "text": "#374151"},
    )

    # style:
    # - Streamlit markdown 안에서 타입별 색을 바로 적용하기 위한 inline CSS 문자열입니다.
    return (
        f"background: {palette['bg']}; "
        f"border-color: {palette['border']}; "
        f"color: {palette['text']};"
    )


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
            (
                f"<span class='type-badge' style='{get_type_badge_style(type_name)}'>"
                f"{escape(type_name)}</span>"
            )
            for type_name in pokemon["types"]
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


def render_team_insights(insights: Dict[str, Any]) -> None:
    """백엔드가 계산한 덱 해석 결과를 요약 카드 형태로 보여주는 함수입니다."""

    if not insights:
        return

    # summary:
    # - 덱 분석에서 가장 먼저 보여줄 한 줄 총평입니다.
    summary = insights.get("summary", "아직 덱 총평을 만들 수 없습니다.")
    team_identity = insights.get("team_identity", "팀 성격 미확인")
    recommendation_direction = insights.get("recommendation_direction", "")

    st.markdown(
        f"""
        <div class="analysis-summary-card">
            <div class="analysis-kicker">덱 총평</div>
            <div class="analysis-title">{escape(team_identity)}</div>
            <div class="analysis-summary-text">{escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    risk_col, strength_col, direction_col = st.columns(3)
    with risk_col:
        st.markdown("**핵심 위험**")
        for item in insights.get("risk_summary", [])[:3]:
            # severity:
            # - high면 더 강한 경고 색상을 적용하기 위한 클래스 값입니다.
            severity = item.get("severity", "medium")
            st.markdown(
                f"""
                <div class="insight-card risk-{escape(severity)}">
                    <div class="insight-card-title">{escape(item.get("title", "위험 요소"))}</div>
                    <div class="insight-card-text">{escape(item.get("detail", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with strength_col:
        st.markdown("**팀 강점**")
        for item in insights.get("strength_summary", [])[:3]:
            st.markdown(
                f"""
                <div class="insight-card strength-card">
                    <div class="insight-card-title">{escape(item.get("title", "강점"))}</div>
                    <div class="insight-card-text">{escape(item.get("detail", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with direction_col:
        st.markdown("**6번째 추천 방향**")
        st.markdown(
            f"""
            <div class="insight-card direction-card">
                <div class="insight-card-title">보완 방향</div>
                <div class="insight-card-text">{escape(recommendation_direction)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        type_balance = insights.get("type_balance", [])
        if type_balance:
            balance_badges = "".join(
                (
                    f"<span class='type-badge' style='{get_type_badge_style(item['type_name'])}'>"
                    f"{escape(item['type_name'])} {item['count']}</span>"
                )
                for item in type_balance[:6]
            )
            st.markdown(
                f"<div class='analysis-type-balance'>{balance_badges}</div>",
                unsafe_allow_html=True,
            )

    role_summary = insights.get("role_summary", [])
    if role_summary:
        with st.expander("선택한 포켓몬 역할 해석"):
            for pokemon in role_summary:
                st.write(f"- {pokemon['name']} | {pokemon['role']} | {pokemon['detail']}")


def render_analysis_result(result: Dict[str, Any]) -> None:
    """팀 분석 API 결과를 사용자가 읽기 좋게 보여주는 함수입니다."""

    st.subheader("포켓몬 덱 분석")

    render_team_insights(result.get("insights", {}))

    selected = result.get("selected_pokemon", [])
    if selected:
        st.markdown("**선택한 포켓몬**")
        for pokemon in selected:
            type_text = ", ".join(type_item["type_name"] for type_item in pokemon.get("types", []))
            st.write(f"- #{pokemon['pokemon_id']:04d} {pokemon['name']} | 타입: {type_text}")

    # weaknesses/resistances:
    # - 백엔드 분석 서비스는 weak_types, resistant_types라는 이름으로 반환합니다.
    # - 혹시 이전 응답 형태가 들어와도 깨지지 않도록 예전 키도 fallback으로 둡니다.
    weaknesses = result.get("weak_types", result.get("weaknesses", []))
    resistances = result.get("resistant_types", result.get("resistances", []))
    move_coverage = result.get("move_type_coverage", [])

    # detail rows:
    # - 위 카드형 분석과 아래 상세 수치가 서로 다른 기준처럼 보이지 않도록 같은 정렬 기준을 사용합니다.
    # - 약점/저항은 score가 높은 순서, 기술 커버리지는 move_count가 많은 순서로 보여줍니다.
    weaknesses = sorted(weaknesses, key=lambda item: item.get("score", 0), reverse=True)
    resistances = sorted(resistances, key=lambda item: item.get("score", 0), reverse=True)
    move_coverage = sorted(move_coverage, key=lambda item: item.get("move_count", 0), reverse=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**주의할 약점 타입**")
        if weaknesses:
            for item in weaknesses[:8]:
                st.write(
                    f"- {item['type_name']}: 위험 {item.get('score', 0)}점 "
                    f"(평균 {item.get('average_multiplier', 0):.2f}배)"
                )
        else:
            st.caption("큰 약점 타입이 아직 계산되지 않았어요.")

    with col2:
        st.markdown("**방어가 좋은 타입**")
        if resistances:
            for item in resistances[:8]:
                st.write(
                    f"- {item['type_name']}: 안정 {item.get('score', 0)}점 "
                    f"(평균 {item.get('average_multiplier', 0):.2f}배)"
                )
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
        .analysis-summary-card {
            margin: 16px 0 18px 0;
            padding: 22px 24px;
            border: 1px solid #c7d2fe;
            border-radius: 22px;
            background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 58%, #ecfeff 100%);
            box-shadow: 0 14px 32px rgba(30, 41, 59, 0.08);
        }
        .analysis-kicker {
            color: #2563eb;
            font-size: 13px;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .analysis-title {
            margin-top: 4px;
            color: #111827;
            font-size: 24px;
            font-weight: 900;
        }
        .analysis-summary-text {
            margin-top: 8px;
            color: #334155;
            font-size: 16px;
            line-height: 1.65;
            font-weight: 650;
        }
        .insight-card {
            min-height: 110px;
            margin: 10px 0;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid #d8dee9;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 10px 24px rgba(30, 41, 59, 0.07);
        }
        .risk-high {
            border-color: #fecaca;
            background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
        }
        .risk-medium {
            border-color: #fed7aa;
            background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
        }
        .strength-card {
            border-color: #bbf7d0;
            background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
        }
        .direction-card {
            border-color: #bae6fd;
            background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
        }
        .insight-card-title {
            color: #111827;
            font-size: 15px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .insight-card-text {
            color: #475569;
            font-size: 14px;
            line-height: 1.55;
            font-weight: 650;
        }
        .analysis-type-balance {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
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
