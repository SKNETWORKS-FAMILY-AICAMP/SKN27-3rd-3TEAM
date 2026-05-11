# Type
    - 속성
        "type_id": row["id"],
        "name": row["name"],
    - 관계
        - Efficacy -> Type

# Pokemon
    - 속성
        "pokemon_id": pokemon["id"],
        "name": pokemon["name"],
        "height": pokemon.get("height"),
        "weight": pokemon.get("weight"),
        "base_exp": pokemon.get("base_exp"),
        "image_url": pokemon.get("image_url"),
        "cry_url": pokemon.get("cry_url"),
        "is_default": pokemon.get("is_default", True),
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "sp_attack": sp_attack,
        "sp_defense": sp_defense,
        "speed": speed,
        "base_total": hp + attack + defense + sp_attack + sp_defense + speed,
    - 관계
        - HasType -> Type
        - CanKnow -> Move
        - CanHave -> Ability

# Move
    - 속성
        "move_id": row["id"],
        "name": row["name"],

        "type_id": row.get("type_id"),

        "power": row.get("power"),
        "accuracy": row.get("accuracy"),
        "damage_class": row.get("damage_class"),
        "effect_text": row.get("effect_text"),

        # 추가 고려 사항
        pp, 우선도, 메타(상태이상, 상태이상 확률, 카테고리, 급소율, 흡혈율, 풀죽을확률, 치유량, 타격횟수, 지속턴수, 스탯 변화 확률), 스탯 변화
    - 관계
        - HasType -> Type

# Ability
    - 속성
        "ability_id": row["id"],
        "name": row["name"],
        "effect_text": row.get("effect_text"),

# Item
    - 속성
        "item_id": row["id"],
        "name": row["name"],
        "category": row.get("category"),
        "effect_text": row.get("effect_text"),

# Nature, species, genereation, ...