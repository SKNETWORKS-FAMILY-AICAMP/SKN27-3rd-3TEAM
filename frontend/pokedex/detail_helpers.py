import os
import urllib.parse

_BASE = os.path.dirname(os.path.abspath(__file__))
TYPE_IMG_DIR = os.path.join(_BASE, "..", "img", "type")

TYPE_FILE_MAP = {"얼음": "아이스"}

KO_TO_EN = {
    "노말": "normal", "풀": "grass", "불꽃": "fire", "물": "water",
    "전기": "electric", "벌레": "bug", "비행": "flying", "바위": "rock",
    "독": "poison", "땅": "ground", "얼음": "ice", "격투": "fighting",
    "에스퍼": "psychic", "고스트": "ghost", "드래곤": "dragon", "악": "dark",
    "강철": "steel", "페어리": "fairy",
}


def get_type_img_src(ko_name: str) -> str:
    filename = TYPE_FILE_MAP.get(ko_name, ko_name)
    path = os.path.join(TYPE_IMG_DIR, f"{filename}.svg")
    try:
        with open(path, "r", encoding="utf-8") as f:
            svg = f.read()
        return f"data:image/svg+xml,{urllib.parse.quote(svg)}"
    except FileNotFoundError:
        return ""


def type_badge_html(ko: str) -> str:
    src = get_type_img_src(ko)
    if src:
        return (
            f'<div style="display:inline-flex;flex-direction:column;align-items:center;'
            f'gap:4px;margin-right:10px;">'
            f'<img src="{src}" width="30" height="30">'
            f'<span style="font-size:0.78rem;font-weight:600;color:#eee;">{ko}</span>'
            f'</div>'
        )
    return f'<span style="font-size:0.9rem;font-weight:600;color:#eee;">{ko}</span>'


def render_evo_node(node, current_pokemon_id, fallback_img=""):
    all_vars = node.get("varieties", [])
    display_vars = [v for v in all_vars if v["is_default"] or any(x in v["name"] for x in ["히스이", "알로라", "가라르", "팔데아"])]
    if not display_vars and all_vars:
        display_vars = [all_vars[0]]

    var_htmls = []
    for v in display_vars:
        v_id, v_name = v["id"], v["name"]
        v_img = v.get("image_url") or fallback_img
        is_active = "active" if v_id == current_pokemon_id else ""
        sorted_types = sorted(v.get("types", []), key=lambda x: x.get("slot", 1))
        v_types_html = "".join([
            f'<div class="evo-type-badge evo-type-{KO_TO_EN.get(t["type_"]["name"], "normal")}">{t["type_"]["name"]}</div>'
            for t in sorted_types
        ])
        var_htmls.append(
            f'<a href="?id={v_id}" target="_self" style="text-decoration:none; color:inherit;">'
            f'<div class="evo-card {is_active}">'
            f'<img src="{v_img}" class="evo-img" alt="{v_name}">'
            f'<div style="font-size:0.8rem; color:rgba(255,255,255,0.6); margin-top:10px; font-weight:600;">No.{v.get("species_id") or v_id:04d}</div>'
            f'<div style="font-weight:800; font-size:0.95rem; color:#fff; margin-bottom:12px; font-family:\'Outfit\', sans-serif; word-break:keep-all; overflow-wrap:break-word; max-width:170px;">{v_name}</div>'
            f'<div style="display:flex; justify-content:center; gap:6px;">{v_types_html}</div>'
            f'</div></a>'
        )

    varieties_block = "".join(var_htmls)
    step_html = f'<div style="display:flex; flex-direction:column; align-items:center; gap:10px;">{varieties_block}</div>'

    children = node.get("evolves_to", [])
    if children:
        child_htmls = [render_evo_node(child, current_pokemon_id, fallback_img) for child in children]
        children_combined = "".join([
            f'<div style="display:flex; align-items:center; gap:15px;"><div class="evo-arrow">▶</div>{ch}</div>'
            for ch in child_htmls
        ])
        return f'<div style="display:flex; align-items:center; gap:15px;">{step_html}<div style="display:flex; flex-direction:column; gap:25px;">{children_combined}</div></div>'
    return step_html
