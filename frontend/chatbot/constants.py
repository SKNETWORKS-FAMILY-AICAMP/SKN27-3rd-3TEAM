from chatbot.api import fetch_models

MODELS_LIST, DEFAULT_MODEL = fetch_models()

MODEL_DISPLAY_NAMES = {
    "gpt-4o-mini": "빠른 모델",
    "gemma4:e2b":  "사고 모델",
}

_TOOL_COLORS = {
    "search_pokemon_db":      ("#3B4CCA", "rgba(59,76,202,0.15)"),
    "search_flavor_text":     ("#7c3aed", "rgba(124,58,237,0.15)"),
    "search_evolution_chain": ("#059669", "rgba(5,150,105,0.15)"),
    "search_type_relations":  ("#d97706", "rgba(217,119,6,0.15)"),
    "web_search":             ("#6b7280", "rgba(107,114,128,0.15)"),
}

_TOOL_LABELS = {
    "search_pokemon_db":      "DB 검색",
    "search_flavor_text":     "도감 검색",
    "search_evolution_chain": "진화 체인",
    "search_type_relations":  "타입 상성",
    "web_search":             "웹 검색",
}
