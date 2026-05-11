import json
import os
import re
from typing import Dict, List, Optional, Tuple
from .data import BattlePokemon, HEAL_MOVES, ATTACK_BUFFS
from .engine import type_multiplier, estimate_damage, stat_value

def heuristic_score(attacker: BattlePokemon, defender: BattlePokemon, move: Dict, efficacy: Dict[Tuple[int, int], float]) -> float:
    name = move["name"]
    if name in HEAL_MOVES:
        return 95 * (1 - attacker.current_hp / attacker.max_hp)
    if name in ATTACK_BUFFS:
        boosted = attacker.attack_stage + attacker.sp_attack_stage + attacker.speed_stage
        return 52 if boosted <= 1 and attacker.current_hp > attacker.max_hp * 0.38 else 14
    return estimate_damage(attacker, defender, move, efficacy) * ((move.get("accuracy") or 100) / 100)

def heuristic_best_move(attacker: BattlePokemon, defender: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> Dict:
    return max(attacker.moves, key=lambda move: heuristic_score(attacker, defender, move, efficacy))

def get_graph_context(bot: BattlePokemon, player: BattlePokemon) -> List[Dict]:
    auth = os.environ.get("NEO4J_AUTH", "neo4j/test1234").split("/")
    user, password = auth[0], auth[1]
    
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=(user, password))
        move_names = [m["name"] for m in bot.moves]
        
        with driver.session() as session:
            query = """
            MATCH (m:Move)-[:HAS_TYPE]->(mt:Type)
            WHERE m.name IN $move_names
            MATCH (p2:Pokemon {name: $opponent_name})-[:HAS_TYPE]->(pt:Type)
            OPTIONAL MATCH (mt)-[eff:ATTACK_EFFECTIVE]->(pt)
            RETURN m.name AS move, mt.name AS move_type, pt.name AS opp_type, coalesce(eff.damage_factor, 1.0) AS factor
            """
            result = session.run(query, move_names=move_names, opponent_name=player.name)
            
            # 결과를 LLM이 이해하기 쉬운 문장 형태로 변환
            context = []
            for record in result:
                factor = record["factor"]
                eff_str = f"보통 (x{factor})"
                if factor >= 2.0: eff_str = f"효과가 굉장함 (x{factor})"
                elif factor == 0.0: eff_str = "효과 없음 (x0)"
                elif factor < 1.0: eff_str = f"효과가 별로임 (x{factor})"
                
                context.append({
                    "move": record["move"],
                    "relation": f"[{record['move']}] 기술({record['move_type']} 타입) -> 상대방({record['opp_type']} 타입) 공격 시 : {eff_str}"
                })
            driver.close()
            return context
    except Exception as e:
        return [{"error": f"GraphDB 연결 실패로 관계 정보를 가져오지 못했습니다. ({e})"}]

def call_llm_for_move(bot: BattlePokemon, player: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> Tuple[Dict, str]:
    fallback = heuristic_best_move(bot, player, efficacy)
    
    # API 키 및 설정 로드
    groq_key = os.environ.get("GROQ_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    # 클라이언트 및 모델 결정 (Groq 우선)
    try:
        from openai import OpenAI
        if groq_key:
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            model = os.environ.get("BATTLE_MODEL", "llama-3.1-8b-instant")
        elif openai_key:
            client = OpenAI(api_key=openai_key)
            model = os.environ.get("BATTLE_MODEL", "gpt-4o-mini")
        else:
            return fallback, "API 키가 없어 전술 폴백 AI가 선택했습니다."

        # Neo4j GraphDB를 통해 상성 관계 조회
        graph_context = get_graph_context(bot, player)

        # 수치 기반 추론 데이터(estimated_damage 등) 제거하고 고유 정보만 남김
        move_context = [
            {
                "id": move["id"],
                "name": move["name"],
                "power": move.get("power"),
                "accuracy": move.get("accuracy"),
            }
            for move in bot.moves
        ]
        
        prompt = {
            "bot": {
                "name": bot.name, "hp": f"{bot.current_hp}/{bot.max_hp}",
                "types": bot.type_names, "stages": {"atk": bot.attack_stage, "spa": bot.sp_attack_stage, "spe": bot.speed_stage}
            },
            "opponent": {
                "name": player.name, "hp": f"{player.current_hp}/{player.max_hp}",
                "types": player.type_names, "speed": stat_value(player, "speed")
            },
            "moves": move_context,
            "graph_database_context": graph_context,
            "instruction": "GraphDB context의 상성 관계를 가장 중요하게 고려하여 최적의 기술 1개를 선택하세요. 이유를 한국어로 작성하세요. Return JSON only."
        }

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a Pokemon battle expert that heavily relies on GraphDB relationships to make decisions. JSON only: {\"move_id\": number, \"reason\": string}"},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            temperature=0.1,
            timeout=10,
        )
        
        content = response.choices[0].message.content or ""
        match = re.search(r"\{.*\}", content, flags=re.S)
        parsed = json.loads(match.group(0) if match else content)
        
        selected_id = int(parsed.get("move_id"))
        selected = next((m for m in bot.moves if m["id"] == selected_id), fallback)
        return selected, parsed.get("reason") or "GraphDB 데이터를 바탕으로 전술적 판단을 내렸습니다."
        
    except Exception as exc:
        return fallback, f"AI 호출 실패로 폴백 엔진 작동 ({exc})"

