"""
봇의 배틀 행동 결정 모듈 (frontend/battle/trainer_bot.py + llm.py 이식)

- decide_random(): 랜덤 전략
- decide_llm():    LLM(Groq) 기반 전략
- decide_action(): 전략 선택 진입점
"""

import os
import json
import re
import random
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

# ── LLM 설정 ─────────────────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

TYPE_MAP = {
    1: '노말', 2: '격투', 3: '비행', 4: '독', 5: '땅', 6: '바위', 7: '벌레',
    8: '고스트', 9: '강철', 10: '불꽃', 11: '물', 12: '풀', 13: '전기',
    14: '에스퍼', 15: '얼음', 16: '드래곤', 17: '악', 18: '페어리'
}

# ── LangGraph 상태 정의 ───────────────────────────────────────────────────────
class BattleState(TypedDict):
    bot_pokemon: Dict[str, Any]
    player_pokemon: Dict[str, Any]
    bot_party: List[Dict[str, Any]]
    analysis: str
    decision: Dict[str, Any]

def _fast_decision_node(state: BattleState) -> Dict[str, Any]:
    """분석과 결정을 단일 노드로 통합 (frontend/battle/llm.py의 fast_decision_node와 동일)"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "당신은 숙련된 포켓몬 배틀 전략가입니다. 상황을 분석하고 즉시 최적의 행동을 결정하세요.\n"
            "응답은 반드시 아래 JSON 형식으로만 출력하세요. 다른 텍스트는 포함하지 마세요.\n"
            "{{\n"
            "  \"analysis\": \"상황 분석 내용\",\n"
            "  \"action_type\": \"move\" 또는 \"switch\",\n"
            "  \"action_name\": \"기술이름(move일 경우)\",\n"
            "  \"action_index\": 인덱스번호(switch일 경우, 0부터 시작)\n"
            "}}"
        )),
        ("user", (
            "### 배틀 상황 ###\n"
            "- **나의 포켓몬**: {bot_name} (타입: {bot_types}, HP: {bot_hp}/{bot_max_hp})\n"
            "- **보유 기술**: {bot_moves}\n\n"
            "- **상대 포켓몬**: {player_name} (타입: {player_types}, HP: {player_hp}/{player_max_hp})\n\n"
            "- **교체 가능한 아군**: {alive_party}\n\n"
            "분석 후 JSON으로 결정을 내리세요."
        ))
    ])

    bot = state['bot_pokemon']
    player = state['player_pokemon']

    alive_party_info = [
        f"[{i}] {p['name']} (타입: {', '.join(p['type_names'])}, HP: {p['current_hp']}/{p['max_hp']})"
        for i, p in enumerate(state['bot_party'])
    ]

    bot_moves_info = []
    for m in bot['moves']:
        t_name = TYPE_MAP.get(m.get('type_id'), '알수없음')
        pwr = m.get('power') or '-'
        acc = m.get('accuracy') or '-'
        dmg_cls = m.get('damage_class', '변화')
        if dmg_cls == 'physical': dmg_cls = '물리'
        elif dmg_cls == 'special': dmg_cls = '특수'
        elif dmg_cls == 'status': dmg_cls = '변화'
        bot_moves_info.append(f"{m['name']}({t_name}/{dmg_cls}/위력:{pwr}/명중:{acc})")

    chain = prompt | llm
    response = chain.invoke({
        "bot_name": bot['name'],
        "bot_types": ", ".join(bot.get('type_names', [])),
        "bot_hp": bot['current_hp'],
        "bot_max_hp": bot['max_hp'],
        "bot_moves": ", ".join(bot_moves_info),
        "player_name": player['name'],
        "player_types": ", ".join(player.get('type_names', [])),
        "player_hp": player['current_hp'],
        "player_max_hp": player['max_hp'],
        "alive_party": "; ".join(alive_party_info) or "없음"
    })

    try:
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {
                "analysis": result.get("analysis", ""),
                "decision": {
                    "action_type": result.get("action_type", "move"),
                    "action_name": result.get("action_name", ""),
                    "action_index": result.get("action_index", 0)
                }
            }
    except Exception:
        pass

    return {
        "analysis": "분석 실패",
        "decision": {"action_type": "move", "action_name": bot['moves'][0]['name']}
    }

# 워크플로우를 단일 노드로 단순화하여 오버헤드 감소
_workflow = StateGraph(BattleState)
_workflow.add_node("fast_decision", _fast_decision_node)
_workflow.set_entry_point("fast_decision")
_workflow.add_edge("fast_decision", END)
_battle_graph = _workflow.compile()


# ── 행동 결정 함수 ─────────────────────────────────────────────────────────────

def decide_random(bot_pokemon: Dict[str, Any], bot_party: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    랜덤 전략: 15% 확률로 생존한 다른 포켓몬으로 교체, 그 외에는 무작위 기술 사용.
    frontend/battle/trainer_bot.py _decide_random()과 동일한 로직.
    """
    current_bot_id = bot_pokemon.get("id")
    alive_others = [bp for bp in bot_party if bp.get("id") != current_bot_id and bp.get("current_hp", 0) > 0]

    if alive_others and random.random() < 0.15:
        target_bot = random.choice(alive_others)
        target_idx = bot_party.index(target_bot)
        return {
            "name": f"{target_bot['name']}(으)로 교체",
            "category": "switch",
            "target_index": target_idx,
            "priority": 6,
            "is_bot": True
        }

    return random.choice(bot_pokemon["moves"])


def decide_llm(bot_pokemon: Dict[str, Any], player_pokemon: Dict[str, Any], bot_party: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    LLM 전략: LangGraph를 통해 배틀 상황을 분석하고 최적 행동 결정.
    frontend/battle/trainer_bot.py _decide_llm()과 동일한 로직.
    """
    current_bot_id = bot_pokemon.get("id")
    alive_others = [p for p in bot_party if p.get("id") != current_bot_id and p.get("current_hp", 0) > 0]

    try:
        final_state = _battle_graph.invoke({
            "bot_pokemon": bot_pokemon,
            "player_pokemon": player_pokemon,
            "bot_party": alive_others,
            "analysis": "",
            "decision": {}
        })
        decision = final_state["decision"]

        if decision.get("action_type") == "switch":
            idx = decision.get("action_index", 0)
            if idx < len(alive_others):
                target_bot = alive_others[idx]
                target_idx = bot_party.index(target_bot)
                return {
                    "name": f"{target_bot['name']}(으)로 교체",
                    "category": "switch",
                    "target_index": target_idx,
                    "priority": 6,
                    "is_bot": True
                }

        move_name = decision.get("action_name")
        selected_move = next((m for m in bot_pokemon["moves"] if m["name"] == move_name), None)
        return selected_move if selected_move else random.choice(bot_pokemon["moves"])

    except Exception as e:
        print(f"[BotDecision] LLM error, falling back to random: {e}")
        return decide_random(bot_pokemon, bot_party)


def decide_action(
    bot_pokemon: Dict[str, Any],
    player_pokemon: Dict[str, Any],
    bot_party: List[Dict[str, Any]],
    strategy: str = "llm"
) -> Dict[str, Any]:
    """
    전략 선택 진입점. strategy: 'random' | 'llm' (rag는 llm과 동일)
    """
    if strategy == "random":
        return decide_random(bot_pokemon, bot_party)
    else:
        return decide_llm(bot_pokemon, player_pokemon, bot_party)
