"""
포켓몬 Neo4j 연동 모듈
======================
역할:
  1. PostgreSQL → Neo4j 마이그레이션 (최초 1회)
  2. LangGraph Agent용 Neo4j 툴 2개 제공
     - search_evolution_chain : 진화 체인 탐색
     - search_type_relations  : 타입 상성 탐색

그래프 구조:
  (Pokemon)-[:EVOLVES_TO {min_level, trigger_item}]->(Pokemon)
  (Pokemon)-[:HAS_TYPE]->(Type)
  (Type)-[:STRONG_AGAINST {damage_factor}]->(Type)   # damage_factor >= 200
  (Type)-[:WEAK_AGAINST   {damage_factor}]->(Type)   # damage_factor <= 50

Docker Neo4j 기본 접속:
  bolt://localhost:7687  /  neo4j  /  password
"""

import os
import psycopg2
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_core.tools import tool

load_dotenv()

# ══════════════════════════════════════════════════════════
# 연결 설정
# ══════════════════════════════════════════════════════════

PG_CONN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pokemon_db"
)
if PG_CONN.startswith("postgres://"):
    PG_CONN = PG_CONN.replace("postgres://", "postgresql://", 1)

NEO4J_URI      = os.environ.get("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.environ.get("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD",  "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ══════════════════════════════════════════════════════════
# 마이그레이션 — PostgreSQL → Neo4j (최초 1회만 실행)
# ══════════════════════════════════════════════════════════

def migrate_to_neo4j():
    """
    PostgreSQL의 포켓몬 데이터를 Neo4j 그래프로 마이그레이션합니다.
    최초 1회만 실행하세요. 재실행 시 기존 데이터를 덮어씁니다.

    생성되는 노드/관계:
      (:Pokemon {id, name})
      (:Type    {id, name})
      (:Pokemon)-[:HAS_TYPE]->(:Type)
      (:Pokemon)-[:EVOLVES_TO {min_level, trigger_item}]->(:Pokemon)
      (:Type)-[:STRONG_AGAINST {damage_factor}]->(:Type)
      (:Type)-[:WEAK_AGAINST   {damage_factor}]->(:Type)
    """
    pg = psycopg2.connect(PG_CONN)
    cur = pg.cursor()

    with driver.session() as session:

        # ── 0. 기존 데이터 초기화 ────────────────────────────
        print("기존 Neo4j 데이터 초기화 중...")
        session.run("MATCH (n) DETACH DELETE n")

        # ── 1. Pokemon 노드 ──────────────────────────────────
        print("Pokemon 노드 생성 중...")
        cur.execute("SELECT p.id, p.name, s.id AS species_id FROM pokemon p JOIN species s ON p.id = s.pokemon_id")
        pokemons = cur.fetchall()
        session.run("""
            UNWIND $rows AS row
            MERGE (:Pokemon {id: row.id, name: row.name, species_id: row.species_id})
        """, rows=[{"id": r[0], "name": r[1], "species_id": r[2]} for r in pokemons])
        print(f"  → {len(pokemons)}개 Pokemon 노드 생성")

        # ── 2. Type 노드 ─────────────────────────────────────
        print("Type 노드 생성 중...")
        cur.execute("SELECT id, name FROM types")
        types = cur.fetchall()
        session.run("""
            UNWIND $rows AS row
            MERGE (:Type {id: row.id, name: row.name})
        """, rows=[{"id": r[0], "name": r[1]} for r in types])
        print(f"  → {len(types)}개 Type 노드 생성")

        # ── 3. Pokemon -[:HAS_TYPE]-> Type ───────────────────
        print("HAS_TYPE 관계 생성 중...")
        cur.execute("""
            SELECT pt.pokemon_id, pt.type_id, pt.slot
            FROM pokemon_types pt
        """)
        poke_types = cur.fetchall()
        session.run("""
            UNWIND $rows AS row
            MATCH (p:Pokemon {id: row.pokemon_id})
            MATCH (t:Type    {id: row.type_id})
            MERGE (p)-[:HAS_TYPE {slot: row.slot}]->(t)
        """, rows=[{"pokemon_id": r[0], "type_id": r[1], "slot": r[2]} for r in poke_types])
        print(f"  → {len(poke_types)}개 HAS_TYPE 관계 생성")

        # ── 4. Pokemon -[:EVOLVES_TO]-> Pokemon ──────────────
        print("EVOLVES_TO 관계 생성 중...")
        cur.execute("""
            SELECT
                e.from_species_id,
                e.to_species_id,
                e.min_level,
                i.name AS trigger_item
            FROM evolutions e
            LEFT JOIN items i ON e.trigger_item_id = i.id
        """)
        evolutions = cur.fetchall()
        session.run("""
            UNWIND $rows AS row
            MATCH (from_p:Pokemon {species_id: row.from_species_id})
            MATCH (to_p:Pokemon   {species_id: row.to_species_id})
            MERGE (from_p)-[:EVOLVES_TO {
                min_level:    row.min_level,
                trigger_item: row.trigger_item
            }]->(to_p)
        """, rows=[{
            "from_species_id": r[0],
            "to_species_id":   r[1],
            "min_level":       r[2],
            "trigger_item":    r[3] or "없음"
        } for r in evolutions])
        print(f"  → {len(evolutions)}개 EVOLVES_TO 관계 생성")

        # ── 5. Type 상성 관계 ────────────────────────────────
        # damage_factor: 0=무효, 50=절반, 100=보통, 200=2배
        print("타입 상성 관계 생성 중...")
        cur.execute("""
            SELECT damage_type_id, target_type_id, damage_factor
            FROM type_efficacy
            WHERE damage_factor != 1.0
        """)
        efficacies = cur.fetchall()

        strong = [r for r in efficacies if r[2] >= 2.0]
        weak   = [r for r in efficacies if r[2] <= 0.5]

        session.run("""
            UNWIND $rows AS row
            MATCH (a:Type {id: row.damage_type_id})
            MATCH (b:Type {id: row.target_type_id})
            MERGE (a)-[:STRONG_AGAINST {damage_factor: row.damage_factor}]->(b)
        """, rows=[{"damage_type_id": r[0], "target_type_id": r[1], "damage_factor": r[2]} for r in strong])

        session.run("""
            UNWIND $rows AS row
            MATCH (a:Type {id: row.damage_type_id})
            MATCH (b:Type {id: row.target_type_id})
            MERGE (a)-[:WEAK_AGAINST {damage_factor: row.damage_factor}]->(b)
        """, rows=[{"damage_type_id": r[0], "target_type_id": r[1], "damage_factor": r[2]} for r in weak])

        print(f"  → STRONG_AGAINST {len(strong)}개 / WEAK_AGAINST {len(weak)}개 관계 생성")

        # ── 6. 인덱스 생성 ───────────────────────────────────
        print("인덱스 생성 중...")
        session.run("CREATE INDEX pokemon_name IF NOT EXISTS FOR (p:Pokemon) ON (p.name)")
        session.run("CREATE INDEX type_name    IF NOT EXISTS FOR (t:Type)    ON (t.name)")

    pg.close()
    print("✅ Neo4j 마이그레이션 완료!")


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
                MATCH (prev:Pokemon)-[e:EVOLVES_TO]->(target:Pokemon)
                WHERE target.name CONTAINS $name
                RETURN prev.name AS from_pokemon,
                       target.name AS to_pokemon,
                       e.min_level AS min_level,
                       e.trigger_item AS trigger_item
            """, name=pokemon_name)
            prev_chain = result_prev.data()

            # 진화 후 체인 (이 포켓몬이 무엇으로 진화하는지, 최대 3단계)
            result_next = session.run("""
                MATCH path = (target:Pokemon)-[:EVOLVES_TO*1..3]->(evolved:Pokemon)
                WHERE target.name CONTAINS $name
                RETURN [n IN nodes(path) | n.name] AS chain,
                       [r IN relationships(path) | {
                           min_level:    r.min_level,
                           trigger_item: r.trigger_item
                       }] AS conditions
            """, name=pokemon_name)
            next_chain = result_next.data()

        if not prev_chain and not next_chain:
            return f"{pokemon_name}의 진화 정보를 찾을 수 없습니다. (진화하지 않는 포켓몬일 수 있습니다)"

        lines = [f"🔗 [{pokemon_name}] 진화 체인 정보\n"]

        if prev_chain:
            lines.append("◀ 진화 전:")
            for r in prev_chain:
                cond = f"레벨 {r['min_level']}" if r['min_level'] else f"아이템: {r['trigger_item']}"
                lines.append(f"  {r['from_pokemon']} → {r['to_pokemon']} (조건: {cond})")

        if next_chain:
            lines.append("\n▶ 진화 후:")
            for r in next_chain:
                chain_str = " → ".join(r["chain"])
                cond_parts = []
                for c in r["conditions"]:
                    if c["min_level"]:
                        cond_parts.append(f"Lv.{c['min_level']}")
                    elif c["trigger_item"] and c["trigger_item"] != "없음":
                        cond_parts.append(c["trigger_item"])
                    else:
                        cond_parts.append("?")
                lines.append(f"  {chain_str}  [{' → '.join(cond_parts)}]")

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
            # 이 타입이 강한 상대 (공격 시 2배 이상)
            result_strong = session.run("""
                MATCH (t:Type)-[r:STRONG_AGAINST]->(target:Type)
                WHERE t.name CONTAINS $name
                RETURN target.name AS target, r.damage_factor AS factor
                ORDER BY r.damage_factor DESC
            """, name=type_name)
            strong = result_strong.data()

            # 이 타입이 약한 상대 (공격 시 절반 이하)
            result_weak = session.run("""
                MATCH (t:Type)-[r:WEAK_AGAINST]->(target:Type)
                WHERE t.name CONTAINS $name
                RETURN target.name AS target, r.damage_factor AS factor
                ORDER BY r.damage_factor ASC
            """, name=type_name)
            weak = result_weak.data()

            # 이 타입을 공격할 때 효과적인 타입 (역방향)
            result_vulnerable = session.run("""
                MATCH (attacker:Type)-[r:STRONG_AGAINST]->(t:Type)
                WHERE t.name CONTAINS $name
                RETURN attacker.name AS attacker, r.damage_factor AS factor
                ORDER BY r.damage_factor DESC
            """, name=type_name)
            vulnerable = result_vulnerable.data()

        if not strong and not weak and not vulnerable:
            return f"{type_name} 타입 정보를 찾을 수 없습니다."

        lines = [f"⚔️  [{type_name}] 타입 상성\n"]

        if strong:
            names = ", ".join([f"{r['target']}({r['factor']}배)" for r in strong])
            lines.append(f"✅ 공격 시 효과적 (2배+): {names}")

        if weak:
            names = ", ".join([f"{r['target']}({r['factor']}배)" for r in weak])
            lines.append(f"❌ 공격 시 비효과적 (절반-): {names}")

        if vulnerable:
            names = ", ".join([f"{r['attacker']}({r['factor']}배)" for r in vulnerable])
            lines.append(f"⚠️  이 타입의 약점 (당할 때): {names}")

        return "\n".join(lines)

    except Exception as e:
        return f"타입 상성 검색 오류: {e}"


# ══════════════════════════════════════════════════════════
# 직접 실행 시 마이그레이션
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    migrate_to_neo4j()
