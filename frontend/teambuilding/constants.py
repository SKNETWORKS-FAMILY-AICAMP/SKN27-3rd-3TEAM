import os
from typing import Dict, List, Tuple

BACKEND_API_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"
IS_CLOUD = os.getenv("STREAMLIT_SERVER_PORT") is not None or os.path.exists("/.dockerenv")

REQUIRED_TEAM_SIZE = 5
POKEMON_LIST_SESSION_KEY = "team_builder_pokemon_list"
DEFAULT_API_TIMEOUT = 10
RAG_API_TIMEOUT = 90

TEAM_FILTER_REGIONS: Dict[str, Tuple[int, int]] = {
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

TEAM_FILTER_TYPES: List[Tuple[str, str]] = [
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
