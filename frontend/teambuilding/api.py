from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from .constants import (
    BACKEND_API_URL,
    IS_CLOUD,
    DEFAULT_API_TIMEOUT,
    RAG_API_TIMEOUT,
    POKEMON_LIST_SESSION_KEY,
)


def request_json(method: str, path: str, **kwargs: Any) -> Any:
    urls = [BACKEND_API_URL.rstrip("/")]
    if not IS_CLOUD and BACKEND_API_URL != "http://localhost:8000":
        urls.append("http://localhost:8000")
    urls = list(dict.fromkeys(urls))
    last_error: Optional[Exception] = None

    timeout = kwargs.pop(
        "timeout",
        RAG_API_TIMEOUT if "/rag-" in path else DEFAULT_API_TIMEOUT,
    )

    if path in ("/api/v1/team-builder/rag-analyze", "/api/v1/team-builder/rag-recommend"):
        payload = kwargs.get("json")
        if isinstance(payload, dict) and "user_id" not in payload:
            user_id = get_current_user_id()
            if user_id is not None:
                payload["user_id"] = user_id

    if path == "/api/v1/team-builder/rag-recommend":
        payload = kwargs.get("json")
        if isinstance(payload, dict) and "analysis_result" not in payload:
            analysis_result = st.session_state.get("analysis_result")
            if analysis_result is not None:
                payload["analysis_result"] = analysis_result
                conclusion = extract_final_answer_conclusion(analysis_result)
                if conclusion:
                    payload["analysis_conclusion"] = conclusion

    for base_url in urls:
        try:
            response = requests.request(method, f"{base_url}{path}", timeout=timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise RuntimeError(f"백엔드 API 응답 오류: {exc}") from exc
        except requests.RequestException as exc:
            last_error = exc

    raise RuntimeError(f"백엔드 API 호출 실패: {last_error}")


def get_current_user_id() -> Optional[int]:
    user = st.session_state.get("user")
    if not isinstance(user, dict):
        return None
    db_id = user.get("db_id")
    if db_id is None:
        return None
    return int(db_id)


def extract_final_answer_conclusion(result: Optional[Dict[str, Any]]) -> Optional[str]:
    if not result:
        return None
    final_answer = str(result.get("final_answer") or "").strip()
    if not final_answer:
        return None
    marker = "결론:"
    if marker in final_answer:
        return final_answer[final_answer.find(marker):].split("\n\n", 1)[0].strip()
    return final_answer.split("\n\n", 1)[0].strip()


def get_generation_by_pokemon_id(pokemon_id: int) -> Optional[int]:
    ranges = [
        (1, 151, 1), (152, 251, 2), (252, 386, 3), (387, 493, 4),
        (494, 649, 5), (650, 721, 6), (722, 809, 7), (810, 905, 8), (906, 1025, 9),
    ]
    for start, end, gen in ranges:
        if start <= pokemon_id <= end:
            return gen
    return None


def build_fallback_pokemon_list() -> List[Dict[str, Any]]:
    return [
        {
            "pokemon_id": pid,
            "name": f"Pokemon {pid}",
            "image_url": (
                "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                f"sprites/pokemon/other/official-artwork/{pid}.png"
            ),
            "generation": get_generation_by_pokemon_id(pid),
            "base_total": None,
            "types": [],
            "abilities": [],
        }
        for pid in range(1, 1026)
    ]


def normalize_pokemon_list(raw_data: Any) -> List[Dict[str, Any]]:
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
        pokemon_id = item.get("pokemon_id") or item.get("id")
        if pokemon_id is None:
            continue
        pokemon_id = int(pokemon_id)
        if pokemon_id >= 10000:
            continue

        raw_types = item.get("types") or []
        type_names = []
        for t in raw_types:
            if isinstance(t, dict):
                type_names.append(t.get("type_name") or t.get("name"))
            else:
                type_names.append(str(t))

        raw_abilities = (
            item.get("abilities") or item.get("ability_names")
            or item.get("pokemon_abilities") or []
        )
        if isinstance(raw_abilities, str):
            ability_names = [raw_abilities]
        else:
            ability_names = []
            for a in raw_abilities:
                if isinstance(a, dict):
                    ability_names.append(
                        a.get("ability_name") or a.get("name") or a.get("korean_name")
                    )
                else:
                    ability_names.append(str(a))

        normalized.append({
            "pokemon_id": pokemon_id,
            "name": item.get("name") or item.get("korean_name") or f"Pokemon {pokemon_id}",
            "image_url": item.get("image_url") or item.get("sprite_url") or "",
            "generation": item.get("generation") or item.get("generation_id"),
            "base_total": item.get("base_total"),
            "types": [n for n in type_names if n],
            "abilities": [n for n in ability_names if n],
        })

    return normalized


@st.cache_data(show_spinner=False)
def _fetch_ability_map() -> Dict[int, List[str]]:
    try:
        data = normalize_pokemon_list(request_json("GET", "/api/v1/pokemon/?skip=0&limit=2000"))
        return {p["pokemon_id"]: p.get("abilities", []) for p in data if p.get("abilities")}
    except RuntimeError:
        return {}


def enrich_pokemon_abilities(pokemon_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if any(p.get("abilities") for p in pokemon_list):
        return pokemon_list
    ability_map = _fetch_ability_map()
    if not ability_map:
        return pokemon_list
    for p in pokemon_list:
        p["abilities"] = ability_map.get(p["pokemon_id"], p.get("abilities", []))
    return pokemon_list


def load_pokemon_list() -> List[Dict[str, Any]]:
    cached = st.session_state.get(POKEMON_LIST_SESSION_KEY)
    if cached:
        return cached

    try:
        raw = request_json("GET", "/api/v1/team-builder/pokemon-options")
        normalized = normalize_pokemon_list(raw)
        if normalized:
            normalized = enrich_pokemon_abilities(normalized)
            st.session_state[POKEMON_LIST_SESSION_KEY] = normalized
            return normalized
    except RuntimeError:
        try:
            raw = request_json("GET", "/api/v1/pokemon/")
            normalized = normalize_pokemon_list(raw)
            if any(p["types"] for p in normalized):
                st.session_state[POKEMON_LIST_SESSION_KEY] = normalized
                return normalized
        except RuntimeError:
            pass

    return build_fallback_pokemon_list()


def find_selected_pokemon(
    pokemon_list: List[Dict[str, Any]], selected_ids: List[int]
) -> List[Dict[str, Any]]:
    by_id = {p["pokemon_id"]: p for p in pokemon_list}
    return [by_id[pid] for pid in selected_ids if pid in by_id]
