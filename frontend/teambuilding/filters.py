from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .constants import TEAM_FILTER_REGIONS


def ensure_team_filter_state() -> None:
    defaults = {
        "team_filter_region": "전체",
        "team_filter_dex_range": (1, 1025),
        "team_filter_types": [],
        "team_applied_keyword": "",
        "team_applied_dex_start": 1,
        "team_applied_dex_end": 1025,
        "team_applied_ability": "전체",
        "team_applied_types": [],
        "team_applied_region": "전체",
        "team_pokemon_limit": 50,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_team_search() -> None:
    st.session_state.team_applied_keyword = st.session_state.get("team_input_keyword", "")
    st.session_state.team_applied_ability = st.session_state.get("team_input_ability", "전체")
    rng = st.session_state.get("team_filter_dex_range", (1, 1025))
    st.session_state.team_applied_dex_start = rng[0]
    st.session_state.team_applied_dex_end = rng[1]
    st.session_state.team_applied_types = list(st.session_state.team_filter_types)
    st.session_state.team_applied_region = st.session_state.team_filter_region


def reset_team_filters() -> None:
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
    st.session_state.team_filter_region = region_name
    st.session_state.team_filter_dex_range = TEAM_FILTER_REGIONS.get(region_name, (1, 1025))


def toggle_team_type(type_name: str) -> None:
    selected: List[str] = st.session_state.team_filter_types
    if type_name in selected:
        selected.remove(type_name)
    else:
        selected.append(type_name)


def get_available_abilities(pokemon_list: List[Dict[str, Any]]) -> List[str]:
    abilities = sorted({
        ability
        for p in pokemon_list
        for ability in p.get("abilities", [])
        if ability
    })
    return ["전체"] + abilities


def pokemon_has_ability(pokemon: Dict[str, Any], ability_name: str) -> bool:
    if ability_name == "전체":
        return True
    return ability_name in pokemon.get("abilities", [])


def pokemon_matches_selected_types(pokemon: Dict[str, Any], selected_types: List[str]) -> bool:
    if not selected_types:
        return True
    pokemon_types = set(pokemon.get("types", []))
    return all(t in pokemon_types for t in selected_types)


def filter_team_pokemon_list(pokemon_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    keyword = st.session_state.get("team_applied_keyword", "").strip().lower()
    dex_start = st.session_state.get("team_applied_dex_start", 1)
    dex_end = st.session_state.get("team_applied_dex_end", 1025)
    ability_name = st.session_state.get("team_applied_ability", "전체")
    selected_types = st.session_state.get("team_applied_types", [])

    result = []
    for p in pokemon_list:
        pid = p["pokemon_id"]
        if not dex_start <= pid <= dex_end:
            continue
        if keyword and keyword not in p["name"].lower() and keyword != str(pid):
            continue
        if not pokemon_has_ability(p, ability_name):
            continue
        if not pokemon_matches_selected_types(p, selected_types):
            continue
        result.append(p)
    return result
