"""
items.json에서 held-items / type-enhancement 카테고리 항목을 추출해
item_effects.json을 완성하는 스크립트.

Effects (effects.json 기준):
  1  = 상태이상 부여      (ailment)
  2  = 상태이상 면역      (ailment_immunity)
  3  = 능력치 랭크 변화   (stat_change)
  4  = 능력치 배율 변화   (stat_multiplier)
  5  = 데미지 배율 변화   (damage_modifier)
  6  = 기술 위력 변화     (power_modifier)
  7  = 특정 기술 무효화   (move_immunity)
  8  = 특정 기술 무효+회복/능력상승 (move_absorb)
  9  = HP 회복            (heal)
  10 = 반동 피해          (recoil)

Phases (phases.json 기준):
  1  = on_switch_in
  2  = before_turn
  3  = action_order
  4  = before_move
  5  = accuracy_check
  6  = before_damage
  7  = damage_calculation
  8  = after_damage
  9  = after_move
  10 = end_turn
  11 = on_faint

Stats (stats.json 기준):
  1=hp, 2=attack, 3=defense, 4=sp_attack, 5=sp_defense, 6=speed
  7=accuracy, 8=evasion, 9=critical

Status conditions (status_conditions.json 기준):
  1=마비, 2=잠듦, 3=얼음, 4=화상, 5=독, 6=혼란, 7=헤롱헤롱
"""

import json
from pathlib import Path

BASE = Path(r"c:\dev\project\SKN27-3rd-3TEAM\database\common\data\processed")
GRAPH = Path(r"c:\dev\project\SKN27-3rd-3TEAM\database\graph")

with open(BASE / "items.json", encoding="utf-8") as f:
    items = json.load(f)

TARGET_CATS = {"held-items", "type-enhancement"}

held = [i for i in items if i.get("category") in TARGET_CATS]
print(f"총 {len(held)}개 항목 ({len([i for i in held if i['category']=='type-enhancement'])}개 type-enhancement, "
      f"{len([i for i in held if i['category']=='held-items'])}개 held-items)\n")

for i in held:
    print(f"  [{i['id']:4d}] [{i['category']:20s}] {i['name']:20s}  {i['effect_text'][:50]}")
