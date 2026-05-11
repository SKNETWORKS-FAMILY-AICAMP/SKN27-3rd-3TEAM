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

def get_graph_context(bot: BattlePokemon, player: BattlePokemon) -> Dict:
    auth = os.environ.get("NEO4J_AUTH", "neo4j/test1234").split("/")
    user, password = auth[0], auth[1]
    
    context = {
        "type_efficacy": [],
        "opponent_info": {},
        "move_effects": []
    }
    
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=(user, password))
        move_names = [m["name"] for m in bot.moves]
        
        with driver.session() as session:
            # 1. 타입 상성 (Type Efficacy)
            query_eff = """
            MATCH (m:Move)-[:HAS_TYPE]->(mt:Type)
            WHERE m.name IN $move_names
            MATCH (p2:Pokemon {name: $opponent_name})-[:HAS_TYPE]->(pt:Type)
            OPTIONAL MATCH (mt)-[eff:ATTACK_EFFECTIVE]->(pt)
            RETURN m.name AS move, mt.name AS move_type, pt.name AS opp_type, coalesce(eff.damage_factor, 1.0) AS factor
            """
            result_eff = session.run(query_eff, move_names=move_names, opponent_name=player.name)
            for record in result_eff:
                factor = record["factor"]
                eff_str = f"보통 (x{factor})"
                if factor >= 2.0: eff_str = f"효과가 굉장함 (x{factor})"
                elif factor == 0.0: eff_str = "효과 없음 (x0)"
                elif factor < 1.0: eff_str = f"효과가 별로임 (x{factor})"
                
                context["type_efficacy"].append({
                    "move": record["move"],
                    "relation": f"[{record['move']}] 기술({record['move_type']} 타입) -> 상대방({record['opp_type']} 타입) 공격 시 : {eff_str}"
                })
                
            # 2. 상대방 스탯 및 특성 (Opponent Stats & Abilities)
            query_opp = """
            MATCH (p:Pokemon {name: $opponent_name})
            OPTIONAL MATCH (p)-[r:CAN_HAVE]->(a:Ability)
            OPTIONAL MATCH (a)-[rt:TRIGGERS]->(e:Effect)
            RETURN p.hp AS hp, p.attack AS attack, p.defense AS defense, 
                   p.sp_attack AS sp_attack, p.sp_defense AS sp_defense, p.speed AS speed,
                   a.name AS ability_name, r.is_hidden AS is_hidden,
                   collect(DISTINCT e.name) AS effects
            """
            result_opp = session.run(query_opp, opponent_name=player.name)
            opp_stats = {}
            abilities = []
            for record in result_opp:
                if not opp_stats:
                    opp_stats = {
                        "hp": record["hp"], "attack": record["attack"], "defense": record["defense"],
                        "sp_attack": record["sp_attack"], "sp_defense": record["sp_defense"], "speed": record["speed"]
                    }
                if record["ability_name"]:
                    ab_str = f"{record['ability_name']}" + (" (숨겨진 특성)" if record["is_hidden"] else "")
                    if record["effects"] and record["effects"][0] is not None:
                        ab_str += f" - 효과: {', '.join(record['effects'])}"
                    if ab_str not in abilities:
                        abilities.append(ab_str)
            context["opponent_info"] = {"base_stats": opp_stats, "possible_abilities": abilities}
            
            # 3. 기술 부가 효과 및 상태이상 (Move Effects)
            query_moves = """
            MATCH (m:Move)
            WHERE m.name IN $move_names
            OPTIONAL MATCH (m)-[r:TRIGGERS]->(e:Effect)
            OPTIONAL MATCH (e)-[:TRIGGERS]->(sc:StatusCondition)
            OPTIONAL MATCH (e)-[:AFFECTS_STAT]->(st:Stat)
            RETURN m.name AS move, e.name AS effect, r.chance AS chance, r.target AS target, r.phase_id AS phase,
                   sc.name AS status_condition, collect(st.name) AS stat_affected, r.values AS values
            """
            result_moves = session.run(query_moves, move_names=move_names)
            for record in result_moves:
                if record["effect"]:
                    effect_desc = f"[{record['move']}] 기술 부가효과: {record['effect']}"
                    if record["chance"]: effect_desc += f" (발동 확률: {record['chance']}%)"
                    if record["target"]: effect_desc += f" (대상: {record['target']})"
                    if record["status_condition"]: effect_desc += f" -> 상태이상 부여: {record['status_condition']}"
                    if record["stat_affected"] and record["stat_affected"][0] is not None: 
                        effect_desc += f" -> 스탯 변화: {', '.join(record['stat_affected'])} {record['values']}"
                    context["move_effects"].append(effect_desc)
            
            driver.close()
            return context
    except Exception as e:
        return {"error": f"GraphDB 연결 실패로 관계 정보를 가져오지 못했습니다. ({e})"}

def call_llm_for_move(bot: BattlePokemon, player: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> Tuple[Dict, str]:
    # fallback: 모델이 상대의 타입 및 그에 대한 상성과 내가 사용할 수 있는 기술 중 데미지를 계산해서 가장 큰 데미지를 주는 기술을 선택
    # 모델이 알았으면 하는거: 플레이어 현재 체력, 플레이어 타입, 플레이어 포켓몬(능력치, 특성)
    # 기존에는: 현재 체력, 타입 상성, 4개 스킬 정보, 
    fallback = heuristic_best_move(bot, player, efficacy) # -> 기술
    
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
            "instruction": "GraphDB context의 타입 상성, 기술 부가 효과(상태이상, 스탯 랭크 등), 그리고 상대방의 능력치 및 특성을 종합적으로 분석하여 최적의 기술 1개를 선택하세요. 이유를 한국어로 작성하세요. Return JSON only."
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

