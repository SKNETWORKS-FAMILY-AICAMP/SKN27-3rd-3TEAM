import base64
import os

ART = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"
GIF = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown"

_FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_base64_img(file_name: str) -> str:
    for sub in ("main_background", "main_character", ""):
        path = os.path.join(_FRONTEND_DIR, "img", sub, file_name) if sub else os.path.join(_FRONTEND_DIR, "img", file_name)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


def load_backgrounds() -> dict:
    keys = [
        ("main",        "main_background.png"),
        ("pokedex",     "pokedex_background.png"),
        ("battle",      "battle_background.png"),
        ("chatbot",     "chatbot_background.png"),
        ("teambuilding","teambuilding_background.png"),
        ("login",       "login_background.png"),
        ("game1",       "minigame1_background.png"),
        ("game2",       "minigame2_background.png"),
        ("pipigo",      "pipigo_background.png"),
    ]
    return {k: get_base64_img(v) for k, v in keys}


def load_characters() -> dict:
    return {
        "obak":      get_base64_img("Obak.png"),
        "pipigo":    get_base64_img("pipigo.png"),
        "minigame1": get_base64_img("game1.png"),
        "minigame2": get_base64_img("minigame2.png"),
    }
