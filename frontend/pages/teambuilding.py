import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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
# - 클라우드 환경(Streamlit Cloud)이나 Docker에서는 환경 변수를 우선 사용합니다.
BACKEND_API_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

# IS_CLOUD: Streamlit Cloud 환경인지 확인
IS_CLOUD = os.getenv("STREAMLIT_SERVER_PORT") is not None or os.path.exists("/.dockerenv")

# REQUIRED_TEAM_SIZE:
# - 현재 팀 추천 API는 5마리를 선택한 뒤 1마리를 추천하는 흐름이므로 5로 고정합니다.
REQUIRED_TEAM_SIZE = 5

# TEAM_FILTER_REGIONS:
# - 도감 페이지처럼 지방 버튼을 누르면 해당 전국도감 번호 범위만 보이게 하기 위한 기준입니다.
TEAM_FILTER_REGIONS: Dict[str, tuple[int, int]] = {
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

# TEAM_FILTER_TYPES:
# - 팀 빌더 검색 패널의 타입 버튼 순서입니다.
# - 첫 번째 값은 화면에 보이는 한국어 타입명, 두 번째 값은 CSS 색상 클래스에 쓰는 영문 키입니다.
TEAM_FILTER_TYPES = [
    ("노말", "normal"),
    ("풀", "grass"),
    ("불꽃", "fire"),
    ("물", "water"),
    ("전기", "electric"),
    ("벌레", "bug"),
    ("비행", "flying"),
    ("바위", "rock"),
    ("독", "poison"),
    ("땅", "ground"),
    ("얼음", "ice"),
    ("격투", "fighting"),
    ("에스퍼", "psychic"),
    ("고스트", "ghost"),
    ("드래곤", "dragon"),
    ("악", "dark"),
    ("강철", "steel"),
    ("페어리", "fairy"),
]

# POKEMON_LIST_SESSION_KEY:
# - API에서 정상으로 받아온 포켓몬 목록만 세션에 저장하기 위한 key입니다.
# - 임시 fallback 목록은 저장하지 않아야, 백엔드가 복구됐을 때 한국어 이름/타입을 바로 다시 받을 수 있습니다.
POKEMON_LIST_SESSION_KEY = "team_builder_pokemon_list"

# DEFAULT_API_TIMEOUT:
# - 일반 목록 조회/분석 요청은 짧게 끝나므로 기본 timeout을 10초로 둡니다.
DEFAULT_API_TIMEOUT = 10

# RAG_API_TIMEOUT:
# - RAG 추천/분석은 Graph DB, Vector DB, LLM 호출이 함께 실행되어 10초를 넘길 수 있습니다.
# - 사용자가 기다릴 수 있는 범위 안에서 충분히 여유 있게 90초로 둡니다.
RAG_API_TIMEOUT = 90

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
    # - 기본적으로 설정된 백엔드 주소를 사용합니다.
    urls = [BACKEND_API_URL.rstrip("/")]
    
    # 로컬 환경에서만 추가적인 fallback을 고려할 수 있습니다.
    if not IS_CLOUD and BACKEND_API_URL != "http://localhost:8000":
        urls.append("http://localhost:8000")
    
    urls = list(dict.fromkeys(urls))
    last_error: Optional[Exception] = None

    # timeout:
    # - 호출자가 직접 timeout을 넘기면 그 값을 우선 사용합니다.
    # - RAG API는 LLM 응답 시간이 포함되므로 기본 API보다 길게 기다립니다.
    timeout = kwargs.pop(
        "timeout",
        RAG_API_TIMEOUT if "/rag-" in path else DEFAULT_API_TIMEOUT,
    )

    # user_id 자동 추가:
    # - 팀 빌더 저장 로그는 backend의 user_id 컬럼에 로그인 사용자의 DB id를 저장합니다.
    # - 분석/추천 버튼 쪽 payload를 각각 수정하지 않아도, 팀 빌더 RAG 요청이면 여기서 공통으로 붙입니다.
    if path in ("/api/v1/team-builder/rag-analyze", "/api/v1/team-builder/rag-recommend"):
        payload = kwargs.get("json")
        if isinstance(payload, dict) and "user_id" not in payload:
            user_id = get_current_user_id()
            if user_id is not None:
                payload["user_id"] = user_id

    # 추천 저장용 분석 결과 자동 추가:
    # - DB에는 추천이 끝난 시점에 분석 결과와 추천 결과를 한 행으로 같이 저장합니다.
    # - 그래서 추천 API를 호출할 때, 화면에 들고 있던 직전 분석 결과를 함께 보냅니다.
    if path == "/api/v1/team-builder/rag-recommend":
        payload = kwargs.get("json")
        if isinstance(payload, dict) and "analysis_result" not in payload:
            analysis_result = st.session_state.get("analysis_result")
            if analysis_result is not None:
                payload["analysis_result"] = analysis_result
                analysis_conclusion = extract_final_answer_conclusion(analysis_result)
                if analysis_conclusion:
                    payload["analysis_conclusion"] = analysis_conclusion

    for base_url in urls:
        try:
            # response:
            # - method 값에 따라 GET/POST 요청을 모두 처리합니다.
            # - timeout은 백엔드 연결이 오래 멈춰있는 상황을 막기 위한 안전장치입니다.
            response = requests.request(method, f"{base_url}{path}", timeout=timeout, **kwargs)
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


def get_current_user_id() -> Optional[int]:
    """현재 로그인한 사용자의 DB user_id를 session_state에서 꺼내는 함수입니다."""

    # user:
    # - login.py에서 GitHub 로그인 후 st.session_state.user에 저장하는 사용자 정보입니다.
    user = st.session_state.get("user")
    if not isinstance(user, dict):
        return None

    # db_id:
    # - backend users 테이블에 저장된 실제 PK입니다.
    # - 팀 빌더 저장 로그의 user_id에는 GitHub id가 아니라 이 db_id를 넣어야 합니다.
    db_id = user.get("db_id")
    if db_id is None:
        return None

    return int(db_id)


def extract_final_answer_conclusion(result: Optional[Dict[str, Any]]) -> Optional[str]:
    """AI 종합 해설에서 DB에 따로 저장할 첫 결론 문단만 꺼내는 함수입니다."""

    # final_answer:
    # - RAG 분석/추천 API가 반환하는 최종 자연어 해설입니다.
    if not result:
        return None

    final_answer = str(result.get("final_answer") or "").strip()
    if not final_answer:
        return None

    # 결론 문단:
    # - 답변을 두괄식으로 만들었기 때문에 보통 첫 문단이 결론입니다.
    # - 혹시 앞에 다른 문장이 붙어도 "결론:" 이후 첫 문단만 안정적으로 저장합니다.
    conclusion_marker = "결론:"
    if conclusion_marker in final_answer:
        conclusion_text = final_answer[final_answer.find(conclusion_marker):]
        return conclusion_text.split("\n\n", 1)[0].strip()

    return final_answer.split("\n\n", 1)[0].strip()


def build_team_builder_payload(include_limit: bool = False) -> Dict[str, Any]:
    """팀 빌더 분석/추천 API에 보낼 공통 payload를 만드는 함수입니다."""

    # payload:
    # - pokemon_ids는 팀 빌더의 핵심 입력이고, user_id는 로그인 상태일 때만 추가합니다.
    payload: Dict[str, Any] = {"pokemon_ids": st.session_state.selected_pokemon_ids}

    # user_id:
    # - 로그인하지 않은 사용자는 NULL로 저장되도록 아예 보내지 않습니다.
    user_id = get_current_user_id()
    if user_id is not None:
        payload["user_id"] = user_id

    # limit:
    # - 추천 API는 1~3순위 개수를 함께 전달해야 하므로 추천 버튼에서만 추가합니다.
    if include_limit:
        payload["limit"] = 3

    return payload


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
                "abilities": [],
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
        pokemon_id = int(pokemon_id)

        # pokemon_id < 10000:
        # - PokeAPI에서 10000번대 ID는 메가진화/거다이맥스/리전폼 같은 특수 폼이 주로 들어갑니다.
        # - 팀 선택 화면은 기본 포켓몬만 고르게 하기 위해 10000번대 이상은 제외합니다.
        if pokemon_id >= 10000:
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

        # raw_abilities:
        # - API마다 특성 필드명이 다를 수 있어서 여러 후보 이름을 함께 확인합니다.
        # - 현재 팀 빌더 필터에서 특성 검색을 지원하기 위한 보조 데이터입니다.
        raw_abilities = (
            item.get("abilities")
            or item.get("ability_names")
            or item.get("pokemon_abilities")
            or []
        )
        if isinstance(raw_abilities, str):
            ability_names = [raw_abilities]
        else:
            ability_names = []
            for ability_item in raw_abilities:
                if isinstance(ability_item, dict):
                    ability_names.append(
                        ability_item.get("ability_name")
                        or ability_item.get("name")
                        or ability_item.get("korean_name")
                    )
                else:
                    ability_names.append(str(ability_item))

        normalized.append(
            {
                "pokemon_id": pokemon_id,
                "name": item.get("name") or item.get("korean_name") or f"Pokemon {pokemon_id}",
                "image_url": item.get("image_url") or item.get("sprite_url") or "",
                "generation": item.get("generation") or item.get("generation_id"),
                "base_total": item.get("base_total"),
                "types": [name for name in type_names if name],
                "abilities": [name for name in ability_names if name],
            }
        )

    return normalized


def enrich_pokemon_abilities(pokemon_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """가능하면 기존 포켓몬 API에서 특성 정보를 가져와 팀 빌더 목록에 보강하는 함수입니다."""

    # 이미 특성이 있으면 추가 API 호출을 하지 않습니다.
    # - 팀 빌더 전용 API가 abilities를 내려주는 구조로 바뀌면 이 함수는 거의 비용 없이 지나갑니다.
    if any(pokemon.get("abilities") for pokemon in pokemon_list):
        return pokemon_list

    try:
        # ability_source:
        # - 도감/기존 포켓몬 API에 특성 정보가 포함되어 있을 때만 팀 빌더 필터에 활용합니다.
        # - 실패해도 팀 선택 자체는 계속 가능해야 하므로 예외는 아래에서 조용히 무시합니다.
        ability_source = normalize_pokemon_list(
            request_json("GET", "/api/v1/pokemon/?skip=0&limit=2000")
        )
    except RuntimeError:
        return pokemon_list

    ability_by_id = {
        pokemon["pokemon_id"]: pokemon.get("abilities", [])
        for pokemon in ability_source
        if pokemon.get("abilities")
    }
    if not ability_by_id:
        return pokemon_list

    for pokemon in pokemon_list:
        pokemon["abilities"] = ability_by_id.get(pokemon["pokemon_id"], pokemon.get("abilities", []))
    return pokemon_list


def load_pokemon_list() -> List[Dict[str, Any]]:
    """포켓몬 선택 화면에 보여줄 전체 포켓몬 목록을 백엔드에서 가져오는 함수입니다."""

    # cached_list:
    # - 이미 정상 API 응답을 한 번 받아왔다면 같은 화면 rerun에서는 그 목록을 재사용합니다.
    # - st.cache_data를 쓰지 않는 이유는 API 실패 시 만든 임시 목록까지 캐시되어 이름이 Pokemon 1처럼 고정될 수 있기 때문입니다.
    cached_list = st.session_state.get(POKEMON_LIST_SESSION_KEY)
    if cached_list:
        return cached_list

    try:
        # graph_list:
        # - 카드에서 한국어 이름과 타입을 바로 보여주기 위해 Neo4j 목록을 우선 사용합니다.
        # - 기존 /api/v1/pokemon/ 응답은 타입이 비어 있을 수 있어서 후순위로 둡니다.
        raw_data = request_json("GET", "/api/v1/team-builder/pokemon-options")
        normalized = normalize_pokemon_list(raw_data)
        if normalized:
            normalized = enrich_pokemon_abilities(normalized)
            st.session_state[POKEMON_LIST_SESSION_KEY] = normalized
            return normalized
    except RuntimeError:
        try:
            # api_fallback:
            # - 팀빌더 전용 목록 API가 실패할 때만 기존 포켓몬 목록 API를 사용합니다.
            raw_data = request_json("GET", "/api/v1/pokemon/")
            normalized = normalize_pokemon_list(raw_data)
            if any(pokemon["types"] for pokemon in normalized):
                st.session_state[POKEMON_LIST_SESSION_KEY] = normalized
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
    card_class = "pokemon-card team-picker-card selected-card" if is_selected else "pokemon-card team-picker-card"

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
    # - 도감 페이지 카드와 화면 언어를 맞추기 위해 No.번호, 이름, 타입 순서로 구성합니다.
    # - 선택 버튼은 Streamlit 버튼으로 따로 렌더링해야 클릭 상태를 안정적으로 처리할 수 있습니다.
    card_html = f"""
    <div class="{card_class}">
        <div class="pokemon-image-wrapper">{image_html}</div>
        <div class="pokemon-info">
            <div class="pokemon-id-badge">No.{pokemon["pokemon_id"]:04d}</div>
            <div class="pokemon-card-title">{escape(pokemon["name"])}</div>
            <div class="pokemon-type-row">{type_badges}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # button_label:
    # - 이미 선택된 포켓몬이면 해제, 아니면 선택으로 보여줍니다.
    button_label = "해제" if is_selected else "선택"
    # 버튼은 도감 카드 아래에 붙는 팀빌더 전용 액션입니다.
    st.markdown(
        f"<div class='team-card-button {'selected-action' if is_selected else ''}'>",
        unsafe_allow_html=True,
    )
    st.button(
        button_label,
        key=f"toggle_{pokemon['pokemon_id']}",
        on_click=toggle_pokemon,
        args=(pokemon["pokemon_id"],),
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


_TEAM_ICON_FILENAME_OVERRIDE = {"얼음": "아이스"}


@st.cache_data(show_spinner=False)
def load_team_type_icons() -> dict:
    """SVG 타입 아이콘을 로컬 파일에서 읽어 dict로 반환합니다."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_dir = os.path.join(base_path, "img", "type")
    icons: dict = {}
    for ko, _ in TEAM_FILTER_TYPES:
        filename = _TEAM_ICON_FILENAME_OVERRIDE.get(ko, ko)
        path = os.path.join(icon_dir, f"{filename}.svg")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    icons[ko] = f.read()
            else:
                icons[ko] = ""
        except Exception:
            icons[ko] = ""
    return icons


def ensure_team_filter_state() -> None:
    """팀 빌더 검색 패널에서 사용하는 필터 상태값을 초기화하는 함수입니다."""

    defaults = {
        # 위젯 입력값 (pending)
        "team_filter_region": "전체",
        "team_filter_dex_range": (1, 1025),
        "team_filter_types": [],
        # 실제 결과에 반영되는 값 (applied) — 검색 버튼 클릭 시에만 갱신
        "team_applied_keyword": "",
        "team_applied_dex_start": 1,
        "team_applied_dex_end": 1025,
        "team_applied_ability": "전체",
        "team_applied_types": [],
        "team_applied_region": "전체",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_team_search() -> None:
    """검색 버튼 클릭 시 위젯 입력값을 applied 상태로 복사합니다."""
    st.session_state.team_applied_keyword = st.session_state.get("team_input_keyword", "")
    st.session_state.team_applied_ability = st.session_state.get("team_input_ability", "전체")
    rng = st.session_state.get("team_filter_dex_range", (1, 1025))
    st.session_state.team_applied_dex_start = rng[0]
    st.session_state.team_applied_dex_end = rng[1]
    st.session_state.team_applied_types = list(st.session_state.team_filter_types)
    st.session_state.team_applied_region = st.session_state.team_filter_region


def reset_team_filters() -> None:
    """검색/특성/지방/도감번호/타입 필터를 도감 초기 상태로 되돌리는 함수입니다."""

    st.session_state.team_filter_region = "전체"
    st.session_state.team_filter_dex_range = (1, 1025)
    st.session_state.team_filter_types = []
    st.session_state.team_input_keyword = ""
    st.session_state.team_input_ability = "전체"
    st.session_state.team_applied_keyword = ""
    st.session_state.team_applied_dex_start = 1
    st.session_state.team_applied_dex_end = 1025
    st.session_state.team_applied_ability = "전체"
    st.session_state.team_applied_types = []
    st.session_state.team_applied_region = "전체"


def select_team_region(region_name: str) -> None:
    """지방 버튼을 눌렀을 때 도감번호 범위를 해당 지방 범위로 맞추는 함수입니다."""

    st.session_state.team_filter_region = region_name
    st.session_state.team_filter_dex_range = TEAM_FILTER_REGIONS.get(region_name, (1, 1025))


def toggle_team_type(type_name: str) -> None:
    """타입 버튼을 눌렀을 때 선택/해제를 전환하는 함수입니다."""

    selected_types: List[str] = st.session_state.team_filter_types
    if type_name in selected_types:
        selected_types.remove(type_name)
    else:
        selected_types.append(type_name)


def get_available_abilities(pokemon_list: List[Dict[str, Any]]) -> List[str]:
    """포켓몬 목록에 포함된 특성 이름을 모아 selectbox 옵션으로 만드는 함수입니다."""

    # abilities:
    # - backend가 특성 정보를 내려줄 때만 실제 특성 목록이 채워집니다.
    # - 없으면 "전체"만 보여주어 화면이 깨지지 않게 합니다.
    abilities = sorted(
        {
            ability
            for pokemon in pokemon_list
            for ability in pokemon.get("abilities", [])
            if ability
        }
    )
    return ["전체"] + abilities


def pokemon_has_ability(pokemon: Dict[str, Any], ability_name: str) -> bool:
    """포켓몬이 선택한 특성을 가지고 있는지 확인하는 함수입니다."""

    if ability_name == "전체":
        return True
    return ability_name in pokemon.get("abilities", [])


def pokemon_matches_selected_types(pokemon: Dict[str, Any], selected_types: List[str]) -> bool:
    """선택한 타입 필터를 포켓몬 타입과 비교하는 함수입니다."""

    if not selected_types:
        return True

    # all 조건:
    # - 불꽃 + 비행을 같이 누르면 둘 다 가진 포켓몬을 찾도록 도감형 필터처럼 동작시킵니다.
    pokemon_types = set(pokemon.get("types", []))
    return all(type_name in pokemon_types for type_name in selected_types)


def filter_team_pokemon_list(pokemon_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """검색 패널의 조건을 모두 적용해 카드 영역에 보여줄 포켓몬 목록을 만드는 함수입니다."""

    keyword = st.session_state.get("team_applied_keyword", "").strip().lower()
    dex_start = st.session_state.get("team_applied_dex_start", 1)
    dex_end = st.session_state.get("team_applied_dex_end", 1025)
    ability_name = st.session_state.get("team_applied_ability", "전체")
    selected_types = st.session_state.get("team_applied_types", [])

    filtered: List[Dict[str, Any]] = []
    for pokemon in pokemon_list:
        pokemon_id = pokemon["pokemon_id"]
        pokemon_name = pokemon["name"].lower()

        if not dex_start <= pokemon_id <= dex_end:
            continue
        if keyword and keyword not in pokemon_name and keyword != str(pokemon_id):
            continue
        if not pokemon_has_ability(pokemon, ability_name):
            continue
        if not pokemon_matches_selected_types(pokemon, selected_types):
            continue
        filtered.append(pokemon)

    return filtered


def render_team_filter_panel(pokemon_list: List[Dict[str, Any]]) -> None:
    """도감 페이지 느낌의 검색/특성/지방/도감번호/타입 필터 패널을 그리는 함수입니다."""

    ensure_team_filter_state()
    ability_options = get_available_abilities(pokemon_list)
    if st.session_state.get("team_input_ability", "전체") not in ability_options:
        st.session_state.team_input_ability = "전체"
    if st.session_state.get("team_applied_ability", "전체") not in ability_options:
        st.session_state.team_applied_ability = "전체"

    with st.container(border=True):
        st.markdown('<div class="team-filter-panel-marker"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="team-filter-title">
                <img src="https://pokemonkorea.co.kr/img/_con.ico" class="team-filter-title-icon">
                <span>Team Builder</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        search_col, dex_col = st.columns([1, 1])
        with search_col:
            st.text_input(
                "검색",
                key="team_input_keyword",
                placeholder="포켓몬 이름 또는 번호를 입력하세요.",
                value=st.session_state.get("team_input_keyword", ""),
            )
        with dex_col:
            st.slider(
                "도감번호",
                min_value=1,
                max_value=1025,
                key="team_filter_dex_range",
            )

        left_col, right_col = st.columns([1, 1.7])
        with left_col:
            cur_ability = st.session_state.get("team_input_ability", "전체")
            ability_index = ability_options.index(cur_ability) if cur_ability in ability_options else 0
            st.selectbox(
                "특성",
                ability_options,
                index=ability_index,
                key="team_input_ability",
            )

            st.markdown('<div class="team-filter-label">지방</div>', unsafe_allow_html=True)
            region_names = list(TEAM_FILTER_REGIONS.keys())
            for region_row in (region_names[:5], region_names[5:]):
                region_cols = st.columns(len(region_row))
                for region_col, region_name in zip(region_cols, region_row):
                    with region_col:
                        active_class = (
                            "region-active"
                            if st.session_state.team_filter_region == region_name
                            else ""
                        )
                        st.markdown(
                            f'<div class="team-region-button {active_class}">{escape(region_name)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            "",
                            key=f"team_region_{region_name}",
                            on_click=select_team_region,
                            args=(region_name,),
                            use_container_width=True,
                        )

        type_icons = load_team_type_icons()
        with right_col:
            st.markdown('<div class="team-filter-label">타입</div>', unsafe_allow_html=True)
            for type_row in (
                TEAM_FILTER_TYPES[:6],
                TEAM_FILTER_TYPES[6:12],
                TEAM_FILTER_TYPES[12:18],
            ):
                type_cols = st.columns(len(type_row))
                for type_col, (type_name, type_key) in zip(type_cols, type_row):
                    with type_col:
                        active_class = (
                            "type-active"
                            if type_name in st.session_state.team_filter_types
                            else ""
                        )
                        svg_icon = type_icons.get(type_name, "")
                        icon_html = f'<div class="type-svg-wrap">{svg_icon}</div>' if svg_icon else ""
                        st.markdown(
                            (
                                f'<div class="team-type-button type-bg-{type_key} {active_class}">'
                                f'{icon_html}'
                                f'<span>{escape(type_name)}</span>'
                                f'</div>'
                            ),
                            unsafe_allow_html=True,
                        )
                        st.button(
                            "",
                            key=f"team_type_{type_key}",
                            on_click=toggle_team_type,
                            args=(type_name,),
                            use_container_width=True,
                        )

        _, search_button_col, reset_button_col, _ = st.columns([2, 2, 2, 2])
        with search_button_col:
            st.markdown('<div class="team-filter-search-button"></div>', unsafe_allow_html=True)
            if st.button("검색", key="team_filter_search_action", use_container_width=True):
                apply_team_search()
                st.rerun()
        with reset_button_col:
            st.markdown('<div class="team-filter-reset-button"></div>', unsafe_allow_html=True)
            st.button(
                "초기화",
                key="team_filter_reset_action",
                on_click=reset_team_filters,
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


def render_rag_final_answer(result: Dict[str, Any]) -> None:
    """Hybrid RAG가 만든 최종 자연어 해설을 분석 화면에 추가로 보여주는 함수입니다."""

    # final_answer:
    # - /rag-analyze API가 Graph DB 계산 결과와 Vector DB 근거를 합쳐 만든 최종 설명 문장입니다.
    final_answer = result.get("final_answer")
    if not final_answer:
        return

    # paragraphs:
    # - AI 해설은 길어질 수 있으므로 문단 단위로 나눠 첫 문단을 결론 영역으로 강조합니다.
    # - 스크롤을 내려야 핵심이 보이는 문제를 줄이기 위해, 답변 생성 프롬프트도 결론을 앞에 두도록 맞춥니다.
    paragraphs = [paragraph.strip() for paragraph in str(final_answer).split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return

    conclusion_html = escape(paragraphs[0]).replace(chr(10), "<br>")
    detail_html = "".join(
        f"<p>{escape(paragraph).replace(chr(10), '<br>')}</p>"
        for paragraph in paragraphs[1:]
    )

    st.markdown(
        f"""
        <div class="rag-answer-card">
            <div class="rag-answer-kicker">AI 종합 해설</div>
            <div class="rag-answer-conclusion">{conclusion_html}</div>
            <div class="rag-answer-text">{detail_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_html(html: str) -> str:
    """Streamlit Markdown이 HTML을 코드블록으로 오해하지 않도록 줄 앞 공백을 제거하는 함수입니다."""

    # Markdown 규칙:
    # - 줄 앞에 공백이 많이 있으면 HTML이 아니라 코드블록으로 표시될 수 있습니다.
    # - 카드 UI HTML은 렌더링 직전에 왼쪽 공백을 제거해서 안전하게 표시합니다.
    return "\n".join(line.lstrip() for line in html.splitlines())


def build_type_badges(type_names: List[str]) -> str:
    """타입 이름 목록을 색상 배지 HTML로 바꾸는 함수입니다."""

    # badges:
    # - 포켓몬 카드, 선택 덱 요약, 추천 카드에서 타입을 같은 색상 규칙으로 보여주기 위해 사용합니다.
    badges = []
    for type_name in type_names:
        badges.append(
            f"<span class='type-badge' style='{get_type_badge_style(type_name)}'>"
            f"{escape(type_name)}</span>"
        )

    return "".join(badges) if badges else "<span class='type-placeholder'>타입 정보 없음</span>"


def render_selected_team_cards(selected: List[Dict[str, Any]]) -> None:
    """분석 대상 5마리 포켓몬을 보기 좋은 카드 형태로 보여주는 함수입니다."""

    if not selected:
        return

    # cards:
    # - 기존 글머리표 목록 대신, 사용자가 고른 5마리를 한눈에 확인할 수 있는 요약 카드입니다.
    cards = []
    for pokemon in selected:
        type_names = [
            type_item.get("type_name", "")
            for type_item in pokemon.get("types", [])
            if type_item.get("type_name")
        ]
        image_url = pokemon.get("image_url") or (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
            f"sprites/pokemon/other/official-artwork/{pokemon.get('pokemon_id')}.png"
        )
        image_html = (
            f"<img class='analysis-team-image' src='{escape(image_url)}' alt='{escape(pokemon.get('name', ''))}' />"
            if image_url
            else "<div class='analysis-team-image-empty'>?</div>"
        )

        cards.append(
            normalize_html(
                f"""
                <div class="analysis-team-card">
                    <div class="analysis-team-image-wrap">{image_html}</div>
                    <div class="analysis-team-name">#{pokemon.get('pokemon_id', 0):04d} {escape(pokemon.get('name', ''))}</div>
                    <div class="analysis-team-types">{build_type_badges(type_names)}</div>
                </div>
                """
            )
        )

    st.markdown(
        normalize_html(
            f"""
            <div class="analysis-section-header">선택한 포켓몬</div>
            <div class="analysis-team-grid">
                {''.join(cards)}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_analysis_detail_cards(
    weaknesses: List[Dict[str, Any]],
    resistances: List[Dict[str, Any]],
    move_coverage: List[Dict[str, Any]],
) -> None:
    """약점/방어/기술 커버리지를 카드형 패널로 보여주는 함수입니다."""

    def build_matchup_rows(items: List[Dict[str, Any]], label: str) -> str:
        """타입 상성 목록을 카드 안의 행 HTML로 바꾸는 내부 함수입니다."""

        if not items:
            return "<div class='analysis-empty-row'>아직 계산된 정보가 부족해요.</div>"

        rows = []
        for item in items[:6]:
            type_name = item.get("type_name", "")
            score = item.get("score", 0)
            average = item.get("average_multiplier", 0)
            rows.append(
                normalize_html(
                    f"""
                    <div class="analysis-metric-row">
                        <div class="analysis-metric-left">{build_type_badges([type_name])}</div>
                        <div class="analysis-metric-right">
                            <strong>{label} {score}점</strong>
                            <span>평균 {float(average):.2f}배</span>
                        </div>
                    </div>
                    """
                )
            )
        return "".join(rows)

    def build_coverage_rows(items: List[Dict[str, Any]]) -> str:
        """기술 타입 커버리지 목록을 카드 안의 행 HTML로 바꾸는 내부 함수입니다."""

        if not items:
            return "<div class='analysis-empty-row'>기술 타입 정보가 아직 부족해요.</div>"

        rows = []
        max_count = max((item.get("move_count", 0) for item in items[:6]), default=1)
        for item in items[:6]:
            type_name = item.get("type_name", "")
            move_count = item.get("move_count", 0)
            width = int((move_count / max_count) * 100) if max_count else 0
            rows.append(
                normalize_html(
                    f"""
                    <div class="coverage-row">
                        <div class="coverage-row-top">
                            {build_type_badges([type_name])}
                            <strong>{move_count}개</strong>
                        </div>
                        <div class="coverage-bar">
                            <div class="coverage-bar-fill" style="width:{width}%"></div>
                        </div>
                    </div>
                    """
                )
            )
        return "".join(rows)

    st.markdown(
        normalize_html(
            f"""
            <div class="analysis-detail-grid">
                <div class="analysis-detail-card danger-panel">
                    <div class="analysis-detail-title">주의할 약점 타입</div>
                    <div class="analysis-detail-caption">상대가 이 타입 기술을 들고 오면 교체와 선봉 선택을 조심해야 해요.</div>
                    {build_matchup_rows(weaknesses, "위험")}
                </div>
                <div class="analysis-detail-card safe-panel">
                    <div class="analysis-detail-title">방어가 좋은 타입</div>
                    <div class="analysis-detail-caption">이 타입 공격은 비교적 안정적으로 받아낼 가능성이 높아요.</div>
                    {build_matchup_rows(resistances, "안정")}
                </div>
                <div class="analysis-detail-card coverage-panel">
                    <div class="analysis-detail-title">기술 타입 커버리지</div>
                    <div class="analysis-detail-caption">현재 팀이 어떤 공격 타입을 많이 확보했는지 보여줍니다.</div>
                    {build_coverage_rows(move_coverage)}
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_recommendation_cards(recommendations: List[Dict[str, Any]]) -> None:
    """추천 후보 1~3순위를 카드형 비교 UI로 보여주는 함수입니다."""

    # cards:
    # - 추천 후보를 같은 기준으로 비교할 수 있게 이미지, 점수, 이유를 한 카드에 묶습니다.
    cards = []
    for index, pokemon in enumerate(recommendations[:3], start=1):
        rank = pokemon.get("rank", index)
        score = pokemon.get("hybrid_score", pokemon.get("score", 0))
        image_url = pokemon.get("image_url") or (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
            f"sprites/pokemon/other/official-artwork/{pokemon.get('pokemon_id')}.png"
        )
        reasons = pokemon.get("reasons") or []
        reason_rows = "".join(
            f"<li>{escape(reason)}</li>"
            for reason in reasons[:4]
        ) or "<li>현재 팀의 약점을 보완할 수 있는 후보입니다.</li>"

        raw_types = pokemon.get("types", [])
        type_names = [
            type_item.get("type_name", type_item.get("name", ""))
            if isinstance(type_item, dict)
            else str(type_item)
            for type_item in raw_types
        ]

        image_html = (
            f"<img class='recommend-image' src='{escape(image_url)}' alt='{escape(pokemon.get('name', ''))}' />"
            if image_url
            else "<div class='recommend-image-empty'>?</div>"
        )

        cards.append(
            normalize_html(
                f"""
                <div class="recommend-card rank-{rank}">
                    <div class="recommend-rank">{rank}순위</div>
                    <div class="recommend-image-wrap">{image_html}</div>
                    <div class="recommend-name">#{pokemon.get('pokemon_id', 0):04d} {escape(pokemon.get('name', ''))}</div>
                    <div class="recommend-types">{build_type_badges([name for name in type_names if name])}</div>
                    <div class="recommend-score">추천 점수 <strong>{score}</strong></div>
                    <ul class="recommend-reasons">{reason_rows}</ul>
                </div>
                """
            )
        )

    st.markdown(
        normalize_html(f"<div class='recommend-grid'>{''.join(cards)}</div>"),
        unsafe_allow_html=True,
    )


def render_analysis_result(result: Dict[str, Any]) -> None:
    """팀 분석 API 결과를 사용자가 읽기 좋게 보여주는 함수입니다."""

    st.subheader("포켓몬 덱 분석")

    # analysis:
    # - 기존 /analyze 응답은 분석 값이 바로 오고,
    # - 새 /rag-analyze 응답은 graph_result 안에 기존 분석 값이 들어옵니다.
    # - 이 한 줄로 두 응답 구조를 모두 처리해서 기존 화면 코드를 최대한 유지합니다.
    analysis = result.get("graph_result", result)

    render_team_insights(analysis.get("insights", {}))
    render_rag_final_answer(result)

    selected = analysis.get("selected_pokemon", [])
    render_selected_team_cards(selected)

    # weaknesses/resistances:
    # - 백엔드 분석 서비스는 weak_types, resistant_types라는 이름으로 반환합니다.
    # - 혹시 이전 응답 형태가 들어와도 깨지지 않도록 예전 키도 fallback으로 둡니다.
    weaknesses = analysis.get("weak_types", analysis.get("weaknesses", []))
    resistances = analysis.get("resistant_types", analysis.get("resistances", []))
    move_coverage = analysis.get("move_type_coverage", [])

    # detail rows:
    # - 위 카드형 분석과 아래 상세 수치가 서로 다른 기준처럼 보이지 않도록 같은 정렬 기준을 사용합니다.
    # - 약점/저항은 score가 높은 순서, 기술 커버리지는 move_count가 많은 순서로 보여줍니다.
    weaknesses = sorted(weaknesses, key=lambda item: item.get("score", 0), reverse=True)
    resistances = sorted(resistances, key=lambda item: item.get("score", 0), reverse=True)
    move_coverage = sorted(move_coverage, key=lambda item: item.get("move_count", 0), reverse=True)

    render_analysis_detail_cards(weaknesses, resistances, move_coverage)


def render_recommendation_result(result: Dict[str, Any]) -> None:
    """추천 API 결과를 1~3순위 카드로 보여주는 함수입니다."""

    st.subheader("포켓몬 추천")

    # recommendation_result:
    # - 기존 /recommend 응답은 recommendations가 바로 오고,
    # - 새 /rag-recommend 응답은 reranked_result 안에 최종 추천 목록이 들어옵니다.
    # - 두 구조를 모두 지원해서 기존 추천 카드 UI를 그대로 사용할 수 있게 합니다.
    recommendation_result = result.get("reranked_result", result.get("graph_result", result))

    render_rag_final_answer(result)

    recommendations = recommendation_result.get("recommendations", [])
    if not recommendations:
        st.info("추천 결과가 아직 없어요.")
        return

    render_recommendation_cards(recommendations)


def apply_page_style() -> None:
    """팀 빌더 페이지 전용 CSS를 적용하는 함수입니다."""

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');
        .stApp, .stMarkdown, .stText, .stButton button, .stSelectbox label, .stTextInput label {
            font-size: 18px;
        }
        .stButton button {
            font-weight: 800;
            min-height: 44px;
        }
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
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) {
            background: #2b2b2b !important;
            border: 1px solid #ffffff !important;
            border-radius: 24px !important;
            padding: 24px 28px 28px !important;
            margin: 0 0 28px !important;
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.16) !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) > [data-testid="stVerticalBlock"] {
            background: transparent !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stHorizontalBlock"] {
            align-items: center !important;
        }
        .team-filter-panel-marker {
            position: absolute;
            width: 0;
            height: 0;
            opacity: 0;
            pointer-events: none;
        }
        .team-filter-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0 0 16px;
        }
        .team-filter-title-icon {
            width: 36px;
            height: 36px;
            object-fit: contain;
            filter: drop-shadow(0 2px 6px rgba(227, 53, 53, 0.5));
        }
        .team-filter-title span {
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: 1px;
            text-shadow: 0 2px 8px rgba(227, 53, 53, 0.4);
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) label,
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) label p,
        .team-filter-label {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.1rem !important;
            font-weight: 900 !important;
            color: #ffffff !important;
            letter-spacing: 1px !important;
            text-shadow: 0 2px 6px rgba(227, 53, 53, 0.4) !important;
            margin-bottom: 12px !important;
            display: block !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] [data-baseweb="base-input"],
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stSelectbox"] > div > div {
            background: #1e1e1e !important;
            border: 2px solid #444 !important;
            border-radius: 12px !important;
            color: #e0e0e0 !important;
            min-height: 64px !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] input {
            color: #e0e0e0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 1.25rem !important;
            padding: 22px 28px !important;
            background: transparent !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] input::placeholder {
            color: #666 !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stSelectbox"] span {
            color: #e0e0e0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 1rem !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stSlider"] div[role="slider"] {
            background-color: transparent !important;
            background-image: url("https://pokemonkorea.co.kr/img/_con.ico") !important;
            background-size: 100% 100% !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35) !important;
            width: 34px !important;
            height: 34px !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTickBar"] {
            color: #f8fafc !important;
            font-weight: 800 !important;
        }
        .team-region-button {
            min-height: 38px;
            padding: 8px 8px;
            margin-bottom: 8px;
            border: 1.5px solid #444;
            border-radius: 9px;
            background: #1e1e1e;
            color: #d1d5db;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            font-weight: 850;
            transition: all 0.2s ease;
        }
        .team-region-button.region-active {
            background: #ef3434;
            border-color: #ef3434;
            color: #ffffff;
            box-shadow: 0 0 14px rgba(239, 52, 52, 0.35);
        }
        div[data-testid="stColumn"]:has(.team-region-button) [data-testid="stVerticalBlock"] {
            position: relative;
        }
        div[data-testid="stColumn"]:has(.team-region-button) .element-container:has(button) {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 38px;
            z-index: 10;
            margin: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-region-button) button {
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            border: none !important;
            padding: 0 !important;
        }
        .type-svg-wrap {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            flex-shrink: 0;
        }
        .team-type-button {
            min-height: 48px;
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 12px;
            color: #ffffff;
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-size: 0.85rem;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
            transition: all 0.2s ease;
            position: relative;
            width: 100%;
            cursor: pointer;
        }
        .team-type-button:hover {
            transform: translateY(-3px);
            filter: brightness(1.2);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        }
        .team-type-button span {
            color: #ffffff;
            font-size: 0.85rem;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
            line-height: 1;
        }
        .team-type-button.type-active {
            outline: 3px solid #ffffff;
            outline-offset: 2px;
            box-shadow: 0 0 18px rgba(255, 255, 255, 0.45);
            transform: translateY(-2px);
        }
        .type-bg-normal { background: #A8A77A; }
        .type-bg-fire { background: #EE8130; }
        .type-bg-water { background: #6390F0; }
        .type-bg-electric { background: #F7D02C; color: #111827; text-shadow: none; }
        .type-bg-grass { background: #7AC74C; }
        .type-bg-ice { background: #96D9D9; color: #111827; text-shadow: none; }
        .type-bg-fighting { background: #C22E28; }
        .type-bg-poison { background: #A33EA1; }
        .type-bg-ground { background: #E2BF65; color: #111827; text-shadow: none; }
        .type-bg-flying { background: #A98FF3; }
        .type-bg-psychic { background: #F95587; }
        .type-bg-bug { background: #A6B91A; }
        .type-bg-rock { background: #B6A136; }
        .type-bg-ghost { background: #735797; }
        .type-bg-dragon { background: #6F35FC; }
        .type-bg-dark { background: #705746; }
        .type-bg-steel { background: #B7B7CE; color: #111827; text-shadow: none; }
        .type-bg-fairy { background: #D685AD; }
        div[data-testid="stColumn"]:has(.team-type-button) [data-testid="stVerticalBlock"] {
            position: relative;
        }
        div[data-testid="stColumn"]:has(.team-type-button) .element-container:has(button) {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 48px;
            z-index: 10;
            margin: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-type-button) button {
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            border: none !important;
            padding: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button {
            height: 50px !important;
            border: none !important;
            border-radius: 0 !important;
            transform: skew(-20deg) !important;
            transition: all 0.2s ease !important;
            margin-top: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button div,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button div,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button span,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button span {
            transform: skew(0deg) !important;
            display: inline-block !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            letter-spacing: 1px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button {
            background: #E33535 !important;
            color: #ffffff !important;
            box-shadow: -5px 5px 0 rgba(227, 53, 53, 0.3) !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button span,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button div {
            color: white !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button {
            background: #ffffff !important;
            box-shadow: -5px 5px 0 rgba(0, 0, 0, 0.15) !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button span,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button div {
            color: #1a1a1a !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button:hover {
            background: #ff4d4d !important;
            transform: skew(-20deg) translateY(-2px) !important;
            box-shadow: -8px 8px 0 rgba(227, 53, 53, 0.4) !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button:hover {
            background: #f0f0f0 !important;
            transform: skew(-20deg) translateY(-2px) !important;
            box-shadow: -8px 8px 0 rgba(0, 0, 0, 0.3) !important;
        }
        /* ── Team Side Panel ────────────────────────── */
        .ts-panel {
            background: rgba(20, 20, 30, 0.97);
            border: 1px solid rgba(255,255,255,0.08);
            border-top: 4px solid #FFCB05;
            border-radius: 18px;
            padding: 16px 12px 12px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }
        .ts-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.07);
        }
        .ts-icon {
            width: 24px; height: 24px;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(227,53,53,0.5));
        }
        .ts-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 900;
            color: #FFCB05;
            letter-spacing: 0.5px;
        }
        .ts-badge {
            margin-left: auto;
            background: rgba(255,203,5,0.12);
            border: 1px solid rgba(255,203,5,0.3);
            color: #FFCB05;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 2px 9px;
            border-radius: 20px;
            font-family: 'Outfit', sans-serif;
        }
        /* 2열 3행 그리드 */
        .ts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
            margin-bottom: 10px;
        }
        .ts-slot {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            gap: 4px;
            padding: 8px 4px 7px;
            border-radius: 12px;
            background: rgba(255,255,255,0.025);
            border: 1px dashed rgba(255,255,255,0.09);
            min-height: 92px;
            transition: all 0.2s;
        }
        .ts-slot.filled {
            background: rgba(255,203,5,0.05);
            border: 1px solid rgba(255,203,5,0.22);
        }
        .ts-slot-locked {
            background: rgba(255,255,255,0.01) !important;
            border: 1px dashed rgba(255,255,255,0.05) !important;
            opacity: 0.45;
        }
        .ts-num {
            font-size: 0.52rem;
            font-weight: 800;
            color: #555;
            align-self: flex-start;
            padding-left: 5px;
            line-height: 1;
        }
        .ts-img {
            width: 52px; height: 48px;
            object-fit: contain;
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5));
        }
        .ts-empty-circle {
            width: 40px; height: 40px;
            border: 2px dashed rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: rgba(255,255,255,0.12);
            font-size: 1rem;
        }
        .ts-lock-circle {
            width: 40px; height: 40px;
            border: 2px dashed rgba(255,255,255,0.06);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: rgba(255,255,255,0.12);
            font-size: 1.1rem;
            font-weight: 900;
        }
        .ts-name {
            font-size: 0.62rem;
            font-weight: 700;
            color: #e0e0e0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            width: 100%;
            text-align: center;
            padding: 0 3px;
            font-family: 'Inter', sans-serif;
        }
        .ts-empty-text {
            font-size: 0.58rem;
            font-weight: 600;
            color: rgba(255,255,255,0.18);
            text-align: center;
            font-family: 'Inter', sans-serif;
        }
        .ts-hint {
            text-align: center;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 6px 0 2px;
            font-family: 'Outfit', sans-serif;
            letter-spacing: 0.2px;
        }

        /* ── Team Action Buttons ─────────────────────── */
        .element-container:has(.tb-act-reset) + .element-container button,
        .element-container:has(.tb-act-analyze) + .element-container button,
        .element-container:has(.tb-act-recommend) + .element-container button {
            height: 44px !important;
            border-radius: 10px !important;
            border: none !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        .element-container:has(.tb-act-reset) + .element-container button {
            background: rgba(255,255,255,0.08) !important;
            color: #aaa !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }
        .element-container:has(.tb-act-reset) + .element-container button:hover {
            background: rgba(255,255,255,0.14) !important;
            color: #fff !important;
        }
        .element-container:has(.tb-act-analyze) + .element-container button {
            background: linear-gradient(135deg, #2a75bb 0%, #FFCB05 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 18px rgba(42,117,187,0.4) !important;
            text-shadow: 0 1px 3px rgba(0,0,0,0.35) !important;
        }
        .element-container:has(.tb-act-analyze) + .element-container button:hover:not(:disabled) {
            filter: brightness(1.12) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(42,117,187,0.5) !important;
        }
        .element-container:has(.tb-act-analyze) + .element-container button:disabled {
            opacity: 0.35 !important;
            cursor: not-allowed !important;
            transform: none !important;
            box-shadow: none !important;
        }

        .selected-count {
            text-align: center;
            color: #2563eb;
            font-weight: 800;
            font-size: 18px;
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
            font-size: 18px;
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
            font-size: 17px;
            font-weight: 800;
            color: #1f2937;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pokemon-card {
            min-height: 250px;
            padding: 16px;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            background: #ffffff;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            display: flex;
            flex-direction: column;
            text-align: left;
            transition: all 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.12);
            margin-bottom: 8px;
            overflow: hidden;
        }
        .team-picker-card:hover {
            transform: translateY(-8px);
            border-color: #d1d5db;
            box-shadow: 0 24px 50px rgba(15, 23, 42, 0.12);
        }
        .selected-card {
            border: 3px solid #2f80ed;
            box-shadow: 0 0 0 4px rgba(47, 128, 237, 0.16), 0 24px 50px rgba(37, 99, 235, 0.16);
        }
        .pokemon-image-wrapper {
            position: relative;
            height: 152px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f9fafb;
            border-radius: 18px;
            margin-bottom: 12px;
        }
        .pokemon-card-image {
            width: 132px;
            height: 132px;
            object-fit: contain;
            filter: drop-shadow(0 10px 18px rgba(15, 23, 42, 0.12));
            transition: transform 0.28s ease;
        }
        .team-picker-card:hover .pokemon-card-image {
            transform: scale(1.08);
        }
        .pokemon-info {
            width: 100%;
            padding: 2px 2px 0;
        }
        .pokemon-id-badge {
            color: #9ca3af;
            font-size: 13px;
            font-weight: 900;
            margin-bottom: 3px;
        }
        .pokemon-card-title {
            width: 100%;
            font-size: 20px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 10px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pokemon-type-row {
            min-height: 30px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 6px;
            flex-wrap: wrap;
        }
        .type-badge {
            flex: 1;
            min-width: 58px;
            padding: 6px 8px;
            border-radius: 7px;
            background: #e0f2fe;
            color: #075985;
            font-size: 14px;
            font-weight: 900;
            text-align: center;
            border: 1px solid #bae6fd;
        }
        .type-placeholder {
            color: #8b95a7;
            font-size: 14px;
            font-weight: 800;
        }
        .team-card-button {
            margin: 0 0 14px;
        }
        .team-card-button button {
            min-height: 42px !important;
            border-radius: 10px !important;
            font-size: 16px !important;
            font-weight: 800 !important;
            background: #ffffff !important;
            border: 1px solid #d1d5db !important;
            color: #111827 !important;
        }
        .team-card-button button:hover {
            border-color: #2563eb !important;
            color: #2563eb !important;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.12) !important;
        }
        .team-card-button.selected-action button {
            border-color: #2563eb !important;
            background: #eff6ff !important;
            color: #1d4ed8 !important;
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
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .analysis-title {
            margin-top: 4px;
            color: #111827;
            font-size: 28px;
            font-weight: 900;
        }
        .analysis-summary-text {
            margin-top: 8px;
            color: #334155;
            font-size: 20px;
            line-height: 1.75;
            font-weight: 650;
        }
        .rag-answer-card {
            margin: 12px 0 20px 0;
            max-height: 360px;
            overflow-y: auto;
            padding: 24px 28px;
            border: 1px solid #a7f3d0;
            border-radius: 20px;
            background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 52%, #ecfeff 100%);
            box-shadow: 0 14px 30px rgba(15, 118, 110, 0.09);
            scrollbar-width: thin;
            scrollbar-color: #34d399 #e2e8f0;
        }
        .rag-answer-card::-webkit-scrollbar {
            width: 10px;
        }
        .rag-answer-card::-webkit-scrollbar-track {
            background: #e2e8f0;
            border-radius: 999px;
        }
        .rag-answer-card::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #34d399 0%, #38bdf8 100%);
            border-radius: 999px;
        }
        .rag-answer-kicker {
            position: sticky;
            top: -24px;
            z-index: 1;
            padding: 0 0 10px 0;
            background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 52%, #ecfeff 100%);
            color: #0f766e;
            font-size: 17px;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .rag-answer-conclusion {
            margin-bottom: 18px;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid #99f6e4;
            background: rgba(240, 253, 250, 0.9);
            color: #0f172a;
            font-size: 22px;
            line-height: 1.65;
            font-weight: 900;
        }
        .rag-answer-text {
            color: #1f2937;
            font-size: 20px;
            line-height: 1.85;
            font-weight: 650;
        }
        .rag-answer-text p {
            margin: 0 0 18px 0;
        }
        .analysis-section-header {
            margin: 22px 0 12px 0;
            color: #111827;
            font-size: 22px;
            font-weight: 900;
        }
        .analysis-team-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 22px;
        }
        .analysis-team-card {
            min-height: 168px;
            padding: 12px;
            border: 1px solid #dbe7f5;
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,251,255,0.92) 100%);
            box-shadow: 0 14px 28px rgba(30, 41, 59, 0.08);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            gap: 8px;
        }
        .analysis-team-image-wrap {
            width: 100%;
            height: 88px;
            border-radius: 16px;
            background: radial-gradient(circle at 50% 35%, #ffffff 0%, #eef6ff 72%);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .analysis-team-image {
            width: 92px;
            height: 84px;
            object-fit: contain;
            filter: drop-shadow(0 8px 10px rgba(30, 41, 59, 0.13));
        }
        .analysis-team-image-empty {
            color: #94a3b8;
            font-weight: 900;
        }
        .analysis-team-name {
            width: 100%;
            color: #111827;
            font-size: 17px;
            font-weight: 900;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .analysis-team-types {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 5px;
        }
        .analysis-detail-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin: 18px 0 32px 0;
        }
        .analysis-detail-card {
            min-height: 360px;
            padding: 18px;
            border-radius: 24px;
            border: 1px solid #dbe7f5;
            box-shadow: 0 18px 36px rgba(30, 41, 59, 0.08);
        }
        .danger-panel {
            background: linear-gradient(180deg, #fff7f7 0%, #ffffff 100%);
            border-color: #fecaca;
        }
        .safe-panel {
            background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
            border-color: #bbf7d0;
        }
        .coverage-panel {
            background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
            border-color: #bfdbfe;
        }
        .analysis-detail-title {
            color: #111827;
            font-size: 22px;
            font-weight: 950;
            margin-bottom: 6px;
        }
        .analysis-detail-caption {
            min-height: 40px;
            color: #64748b;
            font-size: 17px;
            line-height: 1.55;
            font-weight: 700;
            margin-bottom: 14px;
        }
        .analysis-metric-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 11px 0;
            border-top: 1px solid rgba(148, 163, 184, 0.22);
        }
        .analysis-metric-left {
            min-width: 92px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .analysis-metric-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 2px;
            color: #334155;
            font-size: 17px;
            font-weight: 750;
        }
        .analysis-metric-right span {
            color: #64748b;
            font-size: 15px;
            font-weight: 700;
        }
        .analysis-empty-row {
            padding: 16px;
            color: #64748b;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 14px;
            font-weight: 700;
        }
        .coverage-row {
            padding: 11px 0;
            border-top: 1px solid rgba(148, 163, 184, 0.22);
        }
        .coverage-row-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            color: #334155;
            font-size: 17px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .coverage-bar {
            height: 8px;
            border-radius: 999px;
            background: #e2e8f0;
            overflow: hidden;
        }
        .coverage-bar-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        }
        .recommend-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin: 18px 0 32px 0;
        }
        .recommend-card {
            position: relative;
            min-height: 420px;
            padding: 22px 18px 18px 18px;
            border-radius: 28px;
            border: 1px solid #dbe7f5;
            background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,251,255,0.96) 100%);
            box-shadow: 0 20px 42px rgba(30, 41, 59, 0.11);
            overflow: hidden;
        }
        .recommend-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 8px;
            background: linear-gradient(90deg, #60a5fa 0%, #34d399 100%);
        }
        .recommend-card.rank-1::before {
            background: linear-gradient(90deg, #f59e0b 0%, #facc15 100%);
        }
        .recommend-rank {
            color: #111827;
            font-size: 30px;
            font-weight: 950;
            letter-spacing: -0.02em;
            margin-bottom: 10px;
        }
        .recommend-image-wrap {
            height: 150px;
            border-radius: 22px;
            background: radial-gradient(circle at 50% 35%, #ffffff 0%, #eef6ff 76%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
        }
        .recommend-image {
            width: 150px;
            height: 140px;
            object-fit: contain;
            filter: drop-shadow(0 12px 14px rgba(30, 41, 59, 0.16));
        }
        .recommend-image-empty {
            color: #94a3b8;
            font-size: 28px;
            font-weight: 900;
        }
        .recommend-name {
            color: #111827;
            font-size: 21px;
            font-weight: 950;
            margin-bottom: 8px;
        }
        .recommend-types {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            min-height: 26px;
            margin-bottom: 12px;
        }
        .recommend-score {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 14px;
            background: #f1f5f9;
            color: #475569;
            font-size: 17px;
            font-weight: 850;
            margin-bottom: 12px;
        }
        .recommend-score strong {
            color: #2563eb;
            font-size: 22px;
            font-weight: 950;
        }
        .recommend-reasons {
            margin: 0;
            padding-left: 18px;
            color: #334155;
            max-height: 220px;
            overflow-y: auto;
            font-size: 17px;
            line-height: 1.75;
            font-weight: 700;
        }
        .recommend-reasons li {
            margin-bottom: 8px;
        }
        @media (max-width: 1100px) {
            .analysis-team-grid,
            .analysis-detail-grid,
            .recommend-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 720px) {
            .analysis-team-grid,
            .analysis-detail-grid,
            .recommend-grid {
                grid-template-columns: 1fr;
            }
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
            font-size: 19px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .insight-card-text {
            color: #475569;
            font-size: 18px;
            line-height: 1.65;
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


def render_team_side_panel(
    selected_pokemon: List[Dict[str, Any]],
    can_request: bool,
) -> None:
    """우측 팀 패널: 선택 슬롯 5개 + 상태 힌트 + 액션 버튼을 표시합니다."""

    count = len(selected_pokemon)

    # 슬롯 HTML
    # 슬롯 1~5 (선택 가능) + 슬롯 6 (항상 잠금 "?")
    slot_cells = []
    for i in range(REQUIRED_TEAM_SIZE):
        if i < count:
            p = selected_pokemon[i]
            img = escape(p.get("image_url", ""))
            name = escape(p.get("name", ""))
            slot_cells.append(
                f'<div class="ts-slot filled">'
                f'<span class="ts-num">{i + 1}</span>'
                f'<img class="ts-img" src="{img}" alt="{name}">'
                f'<div class="ts-name">{name}</div>'
                f'</div>'
            )
        else:
            slot_cells.append(
                f'<div class="ts-slot">'
                f'<span class="ts-num">{i + 1}</span>'
                f'<div class="ts-empty-circle">＋</div>'
                f'<div class="ts-empty-text">대기</div>'
                f'</div>'
            )

    # 6번째 슬롯 — 덱은 6마리지만 5마리만 선택, 나머지는 자유석
    slot_cells.append(
        f'<div class="ts-slot ts-slot-locked">'
        f'<span class="ts-num">6</span>'
        f'<div class="ts-lock-circle">?</div>'
        f'<div class="ts-empty-text">자유석</div>'
        f'</div>'
    )

    # 상태 힌트
    if count == 0:
        hint, hint_color = "왼쪽에서 포켓몬을 선택하세요", "#555"
    elif count < REQUIRED_TEAM_SIZE:
        hint, hint_color = f"{REQUIRED_TEAM_SIZE - count}마리 더 선택하세요", "#888"
    else:
        hint, hint_color = "팀 분석을 시작하세요!", "#FFCB05"

    st.markdown(
        f"""
        <div class="ts-panel">
            <div class="ts-header">
                <img src="https://pokemonkorea.co.kr/img/_con.ico" class="ts-icon">
                <span class="ts-title">나의 팀</span>
                <span class="ts-badge">{count} / {REQUIRED_TEAM_SIZE}</span>
            </div>
            <div class="ts-grid">
                {"".join(slot_cells)}
            </div>
            <div class="ts-hint" style="color:{hint_color};">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="tb-act-reset">', unsafe_allow_html=True)
    if st.button("선택 초기화", use_container_width=True, key="side_reset"):
        st.session_state.selected_pokemon_ids = []
        st.session_state.analysis_result = None
        st.session_state.recommendation_result = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="tb-act-analyze">', unsafe_allow_html=True)
    if st.button("팀 분석 & 추천", use_container_width=True, disabled=not can_request, key="side_analyze"):
        ids = st.session_state.selected_pokemon_ids

        # 전체화면 로딩 오버레이를 즉시 스트리밍 — API 호출 중 브라우저에 표시됩니다.
        st.markdown(
            """
            <style>
            @keyframes tb-spin { to { transform: rotate(360deg); } }
            @keyframes tb-pulse-ring {
                0%   { transform: scale(0.8); opacity: 0.8; }
                100% { transform: scale(1.6); opacity: 0; }
            }
            .tb-overlay {
                position: fixed; inset: 0;
                background: rgba(5, 5, 15, 0.97);
                z-index: 999999;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                gap: 26px;
            }
            .tb-ball-ring {
                position: relative;
                width: 120px; height: 120px;
                display: flex; align-items: center; justify-content: center;
            }
            .tb-ball-ring::before {
                content: '';
                position: absolute;
                width: 120px; height: 120px;
                border-radius: 50%;
                background: rgba(255, 203, 5, 0.18);
                animation: tb-pulse-ring 1.4s ease-out infinite;
            }
            .tb-ball {
                width: 90px; height: 90px;
                animation: tb-spin 1s linear infinite;
                filter: drop-shadow(0 0 18px rgba(255, 203, 5, 0.35));
                position: relative; z-index: 1;
            }
            .tb-loading-title {
                font-family: 'Outfit', sans-serif;
                font-size: 1.6rem; font-weight: 900;
                color: #ffffff; letter-spacing: 2px;
            }
            .tb-loading-sub {
                font-family: 'Inter', sans-serif;
                font-size: 0.92rem;
                color: rgba(255,255,255,0.35);
                letter-spacing: 0.3px;
                margin-top: -14px;
            }
            </style>
            <div class="tb-overlay">
                <div class="tb-ball-ring">
                    <svg class="tb-ball" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="50" cy="50" r="45" fill="white" stroke="#333" stroke-width="2"/>
                        <path d="M5 50A45 45 0 0 1 95 50H70A20 20 0 0 0 30 50H5" fill="#E33535" stroke="#333" stroke-width="2"/>
                        <circle cx="50" cy="50" r="15" fill="white" stroke="#333" stroke-width="2"/>
                        <circle cx="50" cy="50" r="8" fill="white" stroke="#333" stroke-width="1"/>
                    </svg>
                </div>
                <div class="tb-loading-title">분석 중...</div>
                <div class="tb-loading-sub">팀 전력 분석 및 추천 포켓몬을 계산하고 있어요</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        def _analyze() -> Any:
            return request_json("POST", "/api/v1/team-builder/rag-analyze", json={"pokemon_ids": ids})

        def _recommend() -> Any:
            return request_json("POST", "/api/v1/team-builder/rag-recommend", json={"pokemon_ids": ids, "limit": 3})

        with ThreadPoolExecutor(max_workers=2) as pool:
            f_analyze = pool.submit(_analyze)
            f_recommend = pool.submit(_recommend)
            st.session_state.analysis_result = f_analyze.result()
            st.session_state.recommendation_result = f_recommend.result()

        st.session_state.team_result_type = "both"
        st.switch_page("pages/team_result.py")
    st.markdown("</div>", unsafe_allow_html=True)


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
    # 선택 슬롯은 카드 목록 아래쪽에 다시 배치합니다.

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
                "POST", "/api/v1/team-builder/rag-analyze", json=payload
            )

    with action_col3:
        if st.button("추천 받기", disabled=not can_request, use_container_width=True):
            payload = {"pokemon_ids": st.session_state.selected_pokemon_ids, "limit": 3}
            st.session_state.recommendation_result = request_json(
                "POST", "/api/v1/team-builder/rag-recommend", json=payload
            )

    if st.session_state.analysis_result:
        render_analysis_result(st.session_state.analysis_result)

    if st.session_state.recommendation_result:
        render_recommendation_result(st.session_state.recommendation_result)


def show_v2() -> None:
    """도감형 검색 패널 + 우측 팀 패널을 사용하는 팀 빌더 메인 화면입니다."""

    apply_page_style()

    if "selected_pokemon_ids" not in st.session_state:
        st.session_state.selected_pokemon_ids = []
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "recommendation_result" not in st.session_state:
        st.session_state.recommendation_result = None

    try:
        pokemon_list = load_pokemon_list()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    render_team_filter_panel(pokemon_list)
    filtered_pokemon = filter_team_pokemon_list(pokemon_list)

    selected_pokemon = find_selected_pokemon(pokemon_list, st.session_state.selected_pokemon_ids)
    can_request = len(st.session_state.selected_pokemon_ids) == REQUIRED_TEAM_SIZE

    # 좌우 2분할: 포켓몬 그리드(75%) + 팀 패널(25%)
    grid_col, panel_col = st.columns([3, 1], gap="medium")

    with grid_col:
        with st.container(height=580, border=False):
            grid_columns = st.columns(4)
            for index, pokemon in enumerate(filtered_pokemon):
                with grid_columns[index % 4]:
                    render_pokemon_card(pokemon)

    with panel_col:
        render_team_side_panel(selected_pokemon, can_request)


if __name__ == "__main__":
    show_v2()
