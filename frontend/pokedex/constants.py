REGIONS = ["전체", "관동", "성도", "호연", "신오", "하나", "칼로스", "알로라", "가라르", "팔데아"]

TYPE_ORDER = [
    ("노말", "normal"), ("풀", "grass"),   ("불꽃", "fire"),    ("물", "water"),
    ("전기", "electric"), ("벌레", "bug"), ("비행", "flying"),  ("바위", "rock"),
    ("독", "poison"),   ("땅", "ground"),  ("얼음", "ice"),     ("격투", "fighting"),
    ("에스퍼", "psychic"), ("고스트", "ghost"), ("드래곤", "dragon"), ("악", "dark"),
    ("강철", "steel"),  ("페어리", "fairy"),
]

KO_TO_EN = {ko: en for ko, en in TYPE_ORDER}
EN_TO_KO = {en: ko for ko, en in TYPE_ORDER}

_ICON_FILENAME_OVERRIDE = {"얼음": "아이스"}

REGION_RANGES = {
    "전체":   (1, 1025),
    "관동":   (1, 151),
    "성도":   (152, 251),
    "호연":   (252, 386),
    "신오":   (387, 493),
    "하나":   (494, 649),
    "칼로스": (650, 721),
    "알로라": (722, 809),
    "가라르": (810, 905),
    "팔데아": (906, 1025),
}
