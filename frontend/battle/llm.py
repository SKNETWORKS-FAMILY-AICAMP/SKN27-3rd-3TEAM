import os
import json
import re
from typing import TypedDict, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Groq LLM 설정 (OpenAI 호환 API 사용)
# Groq의 초고속 추론 엔진을 사용하여 응답 속도를 극대화합니다.
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

class BattleState(TypedDict):
    """
    배틀 상태를 유지하는 TypedDict
    """
    bot_pokemon: Dict[str, Any]
    player_pokemon: Dict[str, Any]
    bot_party: List[Dict[str, Any]]
    analysis: str
    decision: Dict[str, Any]

def fast_decision_node(state: BattleState) -> Dict[str, Any]:
    """
    분석과 결정을 하나의 노드로 통합하여 속도를 최적화합니다.
    """
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
    
    # 교체 가능한 아군 상세 정보 구성 (이름 + 타입 + HP)
    alive_party_info = []
    for i, p in enumerate(state['bot_party']):
        info = f"[{i}] {p['name']} (타입: {', '.join(p['type_names'])}, HP: {p['current_hp']}/{p['max_hp']})"
        alive_party_info.append(info)
    
    TYPE_MAP = {
        1: '노말', 2: '격투', 3: '비행', 4: '독', 5: '땅', 6: '바위', 7: '벌레',
        8: '고스트', 9: '강철', 10: '불꽃', 11: '물', 12: '풀', 13: '전기',
        14: '에스퍼', 15: '얼음', 16: '드래곤', 17: '악', 18: '페어리'
    }

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
        "bot_types": ", ".join(bot['type_names']),
        "bot_hp": bot['current_hp'],
        "bot_max_hp": bot['max_hp'],
        "bot_moves": ", ".join(bot_moves_info),
        "player_name": player['name'],
        "player_types": ", ".join(player['type_names']),
        "player_hp": player['current_hp'],
        "player_max_hp": player['max_hp'],
        "alive_party": "; ".join(alive_party_info) or "없음"
    })

    # JSON 추출 및 파싱
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

    # 파싱 실패 시 기본값 (첫 번째 기술 사용)
    return {
        "analysis": "분석 실패",
        "decision": {"action_type": "move", "action_name": bot['moves'][0]['name']}
    }

# 워크플로우를 단일 노드로 단순화하여 오버헤드 감소
workflow = StateGraph(BattleState)
workflow.add_node("fast_decision", fast_decision_node)
workflow.set_entry_point("fast_decision")
workflow.add_edge("fast_decision", END)

battle_graph = workflow.compile()

def get_llm_battle_decision(bot_pokemon: Dict, player_pokemon: Dict, bot_party: List[Dict]) -> Dict:
    """
    BattleBot에서 호출할 인터페이스 함수
    """
    # 현재 살아있는 대기 포켓몬만 필터링 (자기 자신 제외)
    alive_party = [p for p in bot_party if p['id'] != bot_pokemon['id'] and p['current_hp'] > 0]
    
    initial_state = {
        "bot_pokemon": bot_pokemon,
        "player_pokemon": player_pokemon,
        "bot_party": alive_party,
        "analysis": "",
        "decision": {}
    }
    
    final_state = battle_graph.invoke(initial_state)
    return final_state['decision']
