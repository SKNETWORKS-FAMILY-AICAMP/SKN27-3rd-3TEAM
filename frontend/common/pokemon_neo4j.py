"""
포켓몬 Neo4j 연동 모듈
======================
graph_loader.py가 적재한 그래프 스키마에 맞춘 LangGraph Agent 툴:
  - search_evolution_chain : 진화 체인 탐색
  - search_type_relations  : 타입 상성 탐색

그래프 구조 (graph_loader.py 기준):
  (Pokemon)-[:IS_SPECIES]->(Species)
  (Species)-[:EVOLVES_TO {min_level, trigger_item_id}]->(Species)
  (Species)-[:EVOLUTION_REQUIRES]->(Item)
  (Type)-[:ATTACK_EFFECTIVE {damage_factor}]->(Type)
    damage_factor: 0.0=무효, 0.5=절반, 1.0=보통, 2.0=2배
  (Pokemon)-[:HAS_TYPE]->(Type)
  (Pokemon)-[:WEAK_AGAINST / RESISTANT_TO / IMMUNE_TO / ...]->(Type)
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_core.tools import tool

load_dotenv()

NEO4J_URI      = os.environ.get("GRAPH_DB_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.environ.get("GRAPH_DB_USER",     "neo4j")
NEO4J_PASSWORD = os.environ.get("GRAPH_DB_PASSWORD", "test1234")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


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
            # 진화 전 체인 (이 포켓몬이 무엇에서 진화했는지)
            result_prev = session.run("""
                MATCH (prevP:Pokemon)-[:IS_SPECIES]->(prevS:Species)
                      -[e:EVOLVES_TO]->(targetS:Species)<-[:IS_SPECIES]-(targetP:Pokemon)
                WHERE targetP.name CONTAINS $name
                OPTIONAL MATCH (prevS)-[:EVOLUTION_REQUIRES]->(item:Item)
                RETURN prevP.name AS from_pokemon,
                       targetP.name AS to_pokemon,
                       e.min_level AS min_level,
                       item.name AS trigger_item
            """, name=pokemon_name)
            prev_chain = result_prev.data()

            # 진화 후 체인 (이 포켓몬이 무엇으로 진화하는지, 최대 3단계)
            result_next = session.run("""
                MATCH (targetP:Pokemon)-[:IS_SPECIES]->(startS:Species)
                WHERE targetP.name CONTAINS $name
                MATCH path = (startS)-[:EVOLVES_TO*1..3]->(nextS:Species)
                MATCH (nextP:Pokemon)-[:IS_SPECIES]->(nextS)
                RETURN length(path) AS depth,
                       nextP.name AS evolved_name,
                       [r IN relationships(path) | {
                           min_level:       r.min_level,
                           trigger_item_id: r.trigger_item_id
                       }] AS conditions
                ORDER BY depth, evolved_name
            """, name=pokemon_name)
            next_chain = result_next.data()

        if not prev_chain and not next_chain:
            return f"{pokemon_name}의 진화 정보를 찾을 수 없습니다. (진화하지 않는 포켓몬일 수 있습니다)"

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
                        cond_parts.append(f"아이템ID:{c['trigger_item_id']}")
                    else:
                        cond_parts.append("?")
                arrow = " → " * r["depth"]
                lines.append(f"  {pokemon_name}{arrow}{r['evolved_name']}  [{' → '.join(cond_parts)}]")

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
