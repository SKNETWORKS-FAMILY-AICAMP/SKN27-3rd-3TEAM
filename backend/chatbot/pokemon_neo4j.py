"""
포켓몬 Neo4j 연동 모듈
======================
graph_loader.py가 적재한 그래프 스키마에 맞춘 LangGraph Agent 툴:
  - search_evolution_chain : 진화 체인 탐색
  - search_type_relations  : 타입 상성 탐색

노드:
  Pokemon  {pokemon_id, name, species_id, hp, attack, defense, sp_attack, sp_defense, speed, base_total}
  Type     {type_id, name}
  Move     {move_id, name, power, accuracy, damage_class, ...}
  Ability  {ability_id, name, effect_text}
  Item     {item_id, name, category, effect_text}
  Generation {generation_id, name}
  Effect   {effect_id, name, effect_type, effect_text}
  Stat / Ailment / Phase / Weather / Field

관계:
  (Type)-[:ATTACK_EFFECTIVE {damage_factor}]->(Type)     -- 타입 공격 효율 (0.0/0.5/1.0/2.0)
  (Pokemon)-[:HAS_TYPE {slot}]->(Type)
  (Pokemon)-[:EVOLVES_TO {min_level, trigger_item_id}]->(Pokemon)
  (Pokemon)-[:AGAINST {multiplier}]->(Type)              -- 방어 배율 (포괄)
  (Pokemon)-[:WEAK_AGAINST]->(Type)                      -- 2배
  (Pokemon)-[:VERY_WEAK_AGAINST]->(Type)                 -- 4배
  (Pokemon)-[:RESISTANT_TO]->(Type)                      -- 0.5배 이하
  (Pokemon)-[:VERY_RESISTANT_TO]->(Type)                 -- 0.25배 이하
  (Pokemon)-[:IMMUNE_TO]->(Type)                         -- 0배
  (Pokemon)-[:CAN_KNOW {learn_method, level_learned_at}]->(Move)
  (Pokemon)-[:CAN_HAVE {is_hidden, slot}]->(Ability)
  (Pokemon)-[:FROM]->(Generation)
"""

import os
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

# 백엔드의 공용 neo4j_client 재사용 (중복 연결 방지)
try:
    from graph.neo4j_client import neo4j_client as _client
    driver = _client.driver
except ImportError:
    from neo4j import GraphDatabase
    uri = os.getenv("GRAPH_DB_URI") or os.getenv("NEO4J_URI") or "bolt://neo4j:7687"
    user = os.getenv("GRAPH_DB_USER") or os.getenv("NEO4J_USER") or "neo4j"
    password = os.getenv("GRAPH_DB_PASSWORD") or os.getenv("NEO4J_PASSWORD") or "test1234"
    driver = GraphDatabase.driver(uri, auth=(user, password))


# ══════════════════════════════════════════════════════════
# Phase 4-B: 알려진 진화 조건 fallback 맵 (Neo4j 데이터 미수록분)
# ══════════════════════════════════════════════════════════

KNOWN_EVO_CONDITIONS: dict[str, str] = {
    "에스피온":   "낮에 친밀도 MAX",
    "블래키":     "밤에 친밀도 MAX",
    "글레이시아":  "아이템: 얼음의돌",
    "리피아":     "아이템: 이끼의돌",
    "님피아":     "아이템: 요정의돌 또는 낮에 친밀도 MAX + 페어리기술 습득",
    "에브이":     "친밀도 MAX",
    "루카리오":   "낮에 친밀도 MAX",
    "가디안":     "친밀도 MAX",
    "해피너스":   "친밀도 MAX",
    "또가스(갈라르)": "친밀도 MAX",
}


# ══════════════════════════════════════════════════════════
# Agent Tools
# ══════════════════════════════════════════════════════════

@tool
def search_evolution_chain(pokemon_name: str) -> str:
    """
    포켓몬의 진화 체인을 Neo4j 그래프에서 탐색합니다.
    "피카츄 진화", "이브이 진화 경로", "리자몽이 되려면?" 같은 질문에 사용하세요.
    진화 전/후 포켓몬과 진화 조건(레벨, 아이템)을 함께 반환합니다.
    """
    try:
        with driver.session() as session:
            # ── 진화 전 체인 ────────────────────────────────────────
            # (Pokemon)-[:EVOLVES_TO {min_level, trigger_item_id}]->(Pokemon)
            result_prev = session.run("""
                MATCH (prevP:Pokemon)-[e:EVOLVES_TO]->(targetP:Pokemon)
                WHERE targetP.name CONTAINS $name
                WITH prevP, e, targetP LIMIT 1
                OPTIONAL MATCH (triggerItem:Item {item_id: e.trigger_item_id})
                RETURN DISTINCT prevP.name   AS from_pokemon,
                       targetP.name AS to_pokemon,
                       e.min_level  AS min_level,
                       triggerItem.name AS trigger_item
            """, name=pokemon_name)
            prev_chain = result_prev.data()

            # ── 진화 후 체인 (최대 3단계) ───────────────────────────
            # CONTAINS가 여러 폼 노드를 매칭할 수 있으므로 LIMIT 1로 중복 경로 방지
            result_next = session.run("""
                MATCH (targetP:Pokemon)
                WHERE targetP.name CONTAINS $name
                WITH targetP LIMIT 1
                MATCH path = (targetP)-[:EVOLVES_TO*1..3]->(nextP:Pokemon)
                WHERE NOT nextP.name CONTAINS '메가'
                  AND NOT nextP.name CONTAINS '거다이맥스'
                  AND NOT nextP.name CONTAINS 'Mega'
                RETURN DISTINCT length(path) AS depth,
                       nextP.name   AS evolved_name,
                       [r IN relationships(path) | {
                           min_level:       r.min_level,
                           trigger_item_id: r.trigger_item_id
                       }] AS conditions
                ORDER BY depth, evolved_name
            """, name=pokemon_name)
            next_chain = result_next.data()

            # 진화 후 체인에 등장하는 아이템 ID → 이름 일괄 조회
            item_ids = set()
            for row in next_chain:
                for cond in row.get("conditions", []):
                    tid = cond.get("trigger_item_id")
                    if tid:
                        item_ids.add(tid)

            item_name_map: dict = {}
            if item_ids:
                item_result = session.run(
                    "MATCH (i:Item) WHERE i.item_id IN $ids RETURN i.item_id AS id, i.name AS name",
                    ids=list(item_ids),
                )
                item_name_map = {r["id"]: r["name"] for r in item_result.data()}

        if not prev_chain and not next_chain:
            return (
                f"{pokemon_name}의 진화 정보를 찾을 수 없습니다. "
                "(진화하지 않는 포켓몬이거나 이름을 다시 확인해 주세요)"
            )

        lines = [f"🔗 [{pokemon_name}] 진화 체인 정보\n"]

        if prev_chain:
            lines.append("◀ 진화 전:")
            for r in prev_chain:
                if r["min_level"]:
                    cond = f"레벨 {r['min_level']}"
                elif r["trigger_item"]:
                    cond = f"아이템: {r['trigger_item']}"
                else:
                    cond = "조건 미상"
                lines.append(f"  {r['from_pokemon']} → {r['to_pokemon']} (조건: {cond})")

        if next_chain:
            lines.append("\n▶ 진화 후:")
            for r in next_chain:
                cond_parts = []
                for c in r["conditions"]:
                    if c.get("min_level"):
                        cond_parts.append(f"Lv.{c['min_level']}")
                    elif c.get("trigger_item_id"):
                        name = item_name_map.get(c["trigger_item_id"], f"아이템ID:{c['trigger_item_id']}")
                        cond_parts.append(f"아이템: {name}")
                    else:
                        # Phase 4-B: 알려진 진화 조건 fallback
                        known = KNOWN_EVO_CONDITIONS.get(r["evolved_name"])
                        cond_parts.append(known if known else "조건 미상")
                depth_arrow = " → " * r["depth"]
                lines.append(
                    f"  {pokemon_name}{depth_arrow}{r['evolved_name']}"
                    f"  [{' → '.join(cond_parts)}]"
                )

        return "\n".join(lines)

    except Exception as e:
        return f"진화 체인 검색 오류: {e}"


@tool
def search_type_relations(type_name: str) -> str:
    """
    타입 상성 관계를 Neo4j 그래프에서 탐색합니다.
    "불꽃 타입 약점", "물 타입에 강한 타입", "드래곤 타입 상성" 같은 질문에 사용하세요.
    공격/방어 효율과 해당 타입에 약하거나 강한 포켓몬 예시를 함께 반환합니다.
    """
    try:
        with driver.session() as session:
            # 이 타입이 공격 시 효과적인 방어 타입 (2배+)
            # AGAINST: (Pokemon)-[:AGAINST {multiplier}]->(AttackingType)
            # 단일 타입 포켓몬만 사용해 순수 타입 배율을 추출
            strong = session.run("""
                MATCH (attackType:Type)
                WHERE attackType.name CONTAINS $name
                MATCH (p:Pokemon)-[r:AGAINST]->(attackType)
                WHERE r.multiplier >= 2.0
                  AND size([(p)-[:HAS_TYPE]->() | 1]) = 1
                MATCH (p)-[:HAS_TYPE]->(defType:Type)
                WITH defType.name AS target, max(r.multiplier) AS factor
                RETURN target, factor
                ORDER BY factor DESC, target
            """, name=type_name).data()

            # 이 타입이 공격 시 비효과적인 방어 타입 (절반 이하, 무효 제외)
            weak = session.run("""
                MATCH (attackType:Type)
                WHERE attackType.name CONTAINS $name
                MATCH (p:Pokemon)-[r:AGAINST]->(attackType)
                WHERE r.multiplier > 0.0 AND r.multiplier <= 0.5
                  AND size([(p)-[:HAS_TYPE]->() | 1]) = 1
                MATCH (p)-[:HAS_TYPE]->(defType:Type)
                WITH defType.name AS target, min(r.multiplier) AS factor
                RETURN target, factor
                ORDER BY factor ASC, target
            """, name=type_name).data()

            # 이 타입 포켓몬이 당할 때 취약한 공격 타입 (2배+)
            vulnerable = session.run("""
                MATCH (defType:Type)
                WHERE defType.name CONTAINS $name
                MATCH (p:Pokemon)-[:HAS_TYPE]->(defType)
                WHERE size([(p)-[:HAS_TYPE]->() | 1]) = 1
                MATCH (p)-[r:AGAINST]->(attackType:Type)
                WHERE r.multiplier >= 2.0
                WITH attackType.name AS attacker, max(r.multiplier) AS factor
                RETURN attacker, factor
                ORDER BY factor DESC, attacker
            """, name=type_name).data()

            # 이 타입에 약한 포켓몬 예시 (WEAK_AGAINST, 최대 5개)
            weak_pokemon = session.run("""
                MATCH (p:Pokemon)-[:WEAK_AGAINST]->(t:Type)
                WHERE t.name CONTAINS $name
                RETURN p.name AS name
                LIMIT 5
            """, name=type_name).data()

            # 이 타입 공격을 무효(0배)로 막는 방어 타입 (타입 레벨)
            immune_types = session.run("""
                MATCH (attackType:Type)
                WHERE attackType.name CONTAINS $name
                MATCH (p:Pokemon)-[r:AGAINST]->(attackType)
                WHERE r.multiplier = 0.0
                  AND size([(p)-[:HAS_TYPE]->() | 1]) = 1
                MATCH (p)-[:HAS_TYPE]->(defType:Type)
                RETURN DISTINCT defType.name AS target
                ORDER BY target
            """, name=type_name).data()

            # 이 타입에 면역인 포켓몬 예시 (IMMUNE_TO, 최대 5개)
            immune_pokemon = session.run("""
                MATCH (p:Pokemon)-[:IMMUNE_TO]->(t:Type)
                WHERE t.name CONTAINS $name
                RETURN p.name AS name
                LIMIT 5
            """, name=type_name).data()

            # 이 타입 포켓몬이 방어할 때 저항하는 공격 타입 (0 < mult <= 0.5)
            resistant_def = session.run("""
                MATCH (defType:Type)
                WHERE defType.name CONTAINS $name
                MATCH (p:Pokemon)-[:HAS_TYPE]->(defType)
                WHERE size([(p)-[:HAS_TYPE]->() | 1]) = 1
                MATCH (p)-[r:AGAINST]->(attackType:Type)
                WHERE r.multiplier > 0.0 AND r.multiplier <= 0.5
                WITH attackType.name AS attacker, min(r.multiplier) AS factor
                RETURN attacker, factor
                ORDER BY factor ASC, attacker
            """, name=type_name).data()

            # 이 타입 포켓몬이 방어할 때 면역인 공격 타입 (0배)
            immune_def = session.run("""
                MATCH (defType:Type)
                WHERE defType.name CONTAINS $name
                MATCH (p:Pokemon)-[:HAS_TYPE]->(defType)
                WHERE size([(p)-[:HAS_TYPE]->() | 1]) = 1
                MATCH (p)-[r:AGAINST]->(attackType:Type)
                WHERE r.multiplier = 0.0
                WITH attackType.name AS attacker
                RETURN DISTINCT attacker
                ORDER BY attacker
            """, name=type_name).data()

        if not strong and not weak and not vulnerable and not immune_types and not resistant_def:
            return f"{type_name} 타입 정보를 찾을 수 없습니다."

        def fmt(factor: float) -> str:
            if factor == 0.0:
                return "무효"
            return f"{factor:.2g}배"

        lines = [f"⚔️  [{type_name}] 타입 상성\n"]

        if strong:
            names = ", ".join([f"{r['target']}({fmt(r['factor'])})" for r in strong])
            lines.append(f"✅ 공격 시 효과적 (2배+): {names}")

        if weak:
            names = ", ".join([f"{r['target']}({fmt(r['factor'])})" for r in weak])
            lines.append(f"❌ 공격 시 비효과적 (절반-): {names}")

        if immune_types:
            names = ", ".join([r["target"] for r in immune_types])
            lines.append(f"🚫 공격 시 무효 (0배): {names}")

        if vulnerable:
            names = ", ".join([f"{r['attacker']}({fmt(r['factor'])})" for r in vulnerable])
            lines.append(f"⚠️  이 타입의 약점 (당할 때): {names}")

        if immune_def:
            names = ", ".join([r["attacker"] for r in immune_def])
            lines.append(f"✨ 이 타입의 면역 (당할 때 0배): {names}")

        if resistant_def:
            names = ", ".join([f"{r['attacker']}({fmt(r['factor'])})" for r in resistant_def])
            lines.append(f"🛡️  이 타입의 저항 (당할 때 절반-): {names}")

        if weak_pokemon:
            names = ", ".join([r["name"] for r in weak_pokemon])
            lines.append(f"\n📋 약점 포켓몬 예시: {names}")

        if immune_pokemon:
            names = ", ".join([r["name"] for r in immune_pokemon])
            lines.append(f"🛡️  면역 포켓몬 예시: {names}")

        return "\n".join(lines)

    except Exception as e:
        return f"타입 상성 검색 오류: {e}"


@tool
def search_pokemon_weakness(pokemon_name: str) -> str:
    """
    특정 포켓몬의 실제 약점/저항/면역을 조회합니다.
    듀얼 타입의 복합 배율까지 정확히 반영합니다.
    "이상해씨 약점", "피카츄는 뭐가 약해?", "리자몽 타입 상성" 같은 질문에 사용하세요.
    search_type_relations 대신 포켓몬 이름이 주어졌을 때 이 툴을 우선 사용하세요.
    """
    try:
        with driver.session() as session:
            # 포켓몬 타입 확인
            types_result = session.run("""
                MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
                WHERE p.name CONTAINS $name
                RETURN p.name AS pokemon, collect(t.name) AS types
                LIMIT 1
            """, name=pokemon_name).data()

            if not types_result:
                return f"{pokemon_name} 포켓몬을 찾을 수 없습니다."

            pokemon = types_result[0]["pokemon"]
            types = types_result[0]["types"]

            # AGAINST 관계로 실제 배율 조회
            against_result = session.run("""
                MATCH (p:Pokemon)-[r:AGAINST]->(t:Type)
                WHERE p.name CONTAINS $name
                RETURN t.name AS attack_type, r.multiplier AS multiplier
                ORDER BY r.multiplier DESC, t.name
            """, name=pokemon_name).data()

            if not against_result:
                return f"{pokemon}의 타입 상성 데이터를 찾을 수 없습니다."

        def fmt(m: float) -> str:
            return "무효" if m == 0.0 else f"{m:.2g}배"

        buckets = {
            "very_weak": [],   # 4x+
            "weak": [],        # 2x
            "normal": [],      # 1x
            "resistant": [],   # 0.5x
            "very_resistant": [],  # 0.25x
            "immune": [],      # 0x
        }
        for row in against_result:
            m = row["multiplier"]
            t = row["attack_type"]
            if m == 0.0:
                buckets["immune"].append(t)
            elif m >= 4.0:
                buckets["very_weak"].append((t, m))
            elif m >= 2.0:
                buckets["weak"].append((t, m))
            elif m == 1.0:
                buckets["normal"].append(t)
            elif m <= 0.25:
                buckets["very_resistant"].append(t)
            else:
                buckets["resistant"].append(t)

        lines = [f"🔍 [{pokemon}] 타입 상성 (보유 타입: {', '.join(types)})\n"]

        if buckets["very_weak"]:
            names = ", ".join([f"{t}({fmt(m)})" for t, m in buckets["very_weak"]])
            lines.append(f"💀 4배 약점: {names}")
        if buckets["weak"]:
            names = ", ".join([f"{t}({fmt(m)})" for t, m in buckets["weak"]])
            lines.append(f"⚠️  2배 약점: {names}")
        if buckets["resistant"]:
            lines.append(f"🛡️  0.5배 저항: {', '.join(buckets['resistant'])}")
        if buckets["very_resistant"]:
            lines.append(f"🛡️  0.25배 저항: {', '.join(buckets['very_resistant'])}")
        if buckets["immune"]:
            lines.append(f"✨ 면역: {', '.join(buckets['immune'])}")

        return "\n".join(lines)

    except Exception as e:
        return f"포켓몬 약점 검색 오류: {e}"
