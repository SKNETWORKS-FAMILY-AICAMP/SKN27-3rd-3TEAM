"""
포켓몬 Neo4j 연동 모듈
======================
graph_loader.py가 적재한 그래프 스키마에 맞춘 LangGraph Agent 툴:
  - search_evolution_chain : 진화 체인 탐색
  - search_type_relations  : 타입 상성 탐색

그래프 구조 (graph_loader.py 기준):
  (Pokemon {pokemon_id, name, species_id, hp, ...})-[:EVOLVES_TO {min_level, trigger_item_id}]->(Pokemon)
  (Type)-[:ATTACK_EFFECTIVE {damage_factor}]->(Type)
    damage_factor: 0.0=무효, 0.5=절반, 1.0=보통, 2.0=2배
  (Pokemon)-[:HAS_TYPE]->(Type)
  (Pokemon)-[:WEAK_AGAINST / RESISTANT_TO / IMMUNE_TO / ...]->(Type)
  (Item {item_id, name})
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
    driver = GraphDatabase.driver(
        os.environ.get("GRAPH_DB_URI", "bolt://neo4j:7687"),
        auth=(
            os.environ.get("GRAPH_DB_USER", "neo4j"),
            os.environ.get("GRAPH_DB_PASSWORD", "test1234"),
        ),
    )


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
                OPTIONAL MATCH (triggerItem:Item {item_id: e.trigger_item_id})
                RETURN prevP.name   AS from_pokemon,
                       targetP.name AS to_pokemon,
                       e.min_level  AS min_level,
                       triggerItem.name AS trigger_item
            """, name=pokemon_name)
            prev_chain = result_prev.data()

            # ── 진화 후 체인 (최대 3단계) ───────────────────────────
            result_next = session.run("""
                MATCH (targetP:Pokemon)
                WHERE targetP.name CONTAINS $name
                MATCH path = (targetP)-[:EVOLVES_TO*1..3]->(nextP:Pokemon)
                RETURN length(path) AS depth,
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
                        cond_parts.append("조건 미상")
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
    해당 타입이 강한 타입(2배 이상)과 약한 타입(절반 이하)을 반환합니다.
    """
    try:
        with driver.session() as session:
            # 이 타입이 공격 시 효과적인 상대 (2배 이상)
            result_strong = session.run("""
                MATCH (t:Type)-[r:ATTACK_EFFECTIVE]->(target:Type)
                WHERE t.name CONTAINS $name AND r.damage_factor >= 2.0
                RETURN target.name AS target, r.damage_factor AS factor
                ORDER BY r.damage_factor DESC
            """, name=type_name)
            strong = result_strong.data()

            # 이 타입이 공격 시 비효과적인 상대 (절반 이하, 무효 포함)
            result_weak = session.run("""
                MATCH (t:Type)-[r:ATTACK_EFFECTIVE]->(target:Type)
                WHERE t.name CONTAINS $name AND r.damage_factor <= 0.5
                RETURN target.name AS target, r.damage_factor AS factor
                ORDER BY r.damage_factor ASC
            """, name=type_name)
            weak = result_weak.data()

            # 이 타입이 공격받을 때 취약한 타입 (역방향, 2배 이상)
            result_vulnerable = session.run("""
                MATCH (attacker:Type)-[r:ATTACK_EFFECTIVE]->(t:Type)
                WHERE t.name CONTAINS $name AND r.damage_factor >= 2.0
                RETURN attacker.name AS attacker, r.damage_factor AS factor
                ORDER BY r.damage_factor DESC
            """, name=type_name)
            vulnerable = result_vulnerable.data()

        if not strong and not weak and not vulnerable:
            return f"{type_name} 타입 정보를 찾을 수 없습니다."

        def fmt(factor: float) -> str:
            return "무효" if factor == 0.0 else f"{factor}배"

        lines = [f"⚔️  [{type_name}] 타입 상성\n"]

        if strong:
            names = ", ".join([f"{r['target']}({fmt(r['factor'])})" for r in strong])
            lines.append(f"✅ 공격 시 효과적 (2배+): {names}")

        if weak:
            names = ", ".join([f"{r['target']}({fmt(r['factor'])})" for r in weak])
            lines.append(f"❌ 공격 시 비효과적 (절반-): {names}")

        if vulnerable:
            names = ", ".join([f"{r['attacker']}({fmt(r['factor'])})" for r in vulnerable])
            lines.append(f"⚠️  이 타입의 약점 (당할 때): {names}")

        return "\n".join(lines)

    except Exception as e:
        return f"타입 상성 검색 오류: {e}"
