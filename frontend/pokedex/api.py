import os
import requests
import streamlit as st

from pokedex.constants import TYPE_ORDER, _ICON_FILENAME_OVERRIDE

BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"
API_V1_STR = "/api/v1/pokemon"


@st.cache_data(show_spinner=False)
def fetch_abilities():
    try:
        resp = requests.get(f"{BACKEND_URL}{API_V1_STR}/abilities")
        if resp.status_code == 200:
            return ["전체"] + sorted(resp.json())
    except Exception:
        pass
    return ["전체"]


@st.cache_data
def load_type_icons():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_dir = os.path.join(base_path, "img", "type")
    icons = {}
    for ko, _ in TYPE_ORDER:
        filename = _ICON_FILENAME_OVERRIDE.get(ko, ko)
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
