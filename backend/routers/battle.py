from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from battle.common.processor import run_battle_logic
from battle.common.bot_decision import decide_action
from battle.common.constants.leaders import LEADERS as ROSTER_MAP, LEADERS as LEADER_QUOTES
from battle.common.utils.pokemon_loader import load_bot_pokemon

import random

router = APIRouter(
    prefix="/api/v1/battle",
    tags=["battle"],
)

class TurnRequest(BaseModel):
    user_pokemon: Dict[str, Any]
    bot_pokemon: Dict[str, Any]
    bot_party: List[Dict[str, Any]]   # 현재 HP가 반영된 전체 봇 파티
    player_party: List[Dict[str, Any]] = []  # 배틀 종료 판단을 위한 전체 플레이어 파티
    user_move: Dict[str, Any]
    bot_move: Dict[str, Any]
    leader_name: str = "관장"

@router.post("/process_turn")
async def process_turn(request: TurnRequest):
    """
    양측의 포켓몬 상태와 선택한 기술을 받아 1턴을 시뮬레이션하고 결과를 반환합니다.
    봇 포켓몬이 쓰러진 경우, 다음 살아있는 봇의 강제 교체 메시지를 추가로 반환합니다.
    배틀 종료 여부(battle_over)와 승자(winner)도 함께 반환합니다.
    """
    try:
        messages = run_battle_logic(
            request.user_pokemon,
            request.bot_pokemon,
            request.user_move,
            request.bot_move,
            request.leader_name
        )

        # 최종 상태 추출 (run_battle_logic이 dict를 직접 변경하므로 마지막 스냅샷 사용)
        final_p_state = messages[-1]["player_state"]
        final_b_state = messages[-1]["bot_state"]

        # ── 봇 사망 시 강제 교체 메시지 생성 ──────────────────────────────
        # bot_party 중 현재 봇(id 일치)을 제외한 살아있는 포켓몬을 찾아
        # 교체 메시지를 messages 끝에 추가합니다.
        # 프론트엔드 pending_messages 루프는 bot_switch 플래그를 보고
        # 메시지 출력 → 딜레이 → 이미지 갱신 순서로 처리합니다.
        if final_b_state.get("current_hp", 1) <= 0:
            current_bot_id = request.bot_pokemon.get("id")
            alive_bots = [
                (idx, bp)
                for idx, bp in enumerate(request.bot_party)
                if bp.get("id") != current_bot_id and bp.get("current_hp", 0) > 0
            ]
            if alive_bots:
                next_idx, next_bot = alive_bots[0]
                messages.append({
                    "message": f"{request.leader_name}은(는) {next_bot['name']}을(를) 내보냈다!",
                    "player_state": final_p_state,
                    "bot_state": next_bot,
                    "bot_switch": True,
                    "bot_next_index": next_idx,
                })
        # ──────────────────────────────────────────────────────────────────

        # ── 배틀 종료 판단 ─────────────────────────────────────────────────
        battle_over = False
        winner = None

        # 봇 파티 전멸 여부 확인
        current_bot_id = request.bot_pokemon.get("id")
        alive_bots_after = [
            bp for bp in request.bot_party
            if bp.get("current_hp", 0) > 0 and bp.get("id") != current_bot_id
        ]
        bot_all_fainted = final_b_state.get("current_hp", 1) <= 0 and not alive_bots_after

        # 플레이어 파티 전멸 여부 확인
        current_player_id = request.user_pokemon.get("id")
        alive_players_after = [
            pp for pp in request.player_party
            if pp.get("current_hp", 0) > 0 and pp.get("id") != current_player_id
        ]
        player_all_fainted = final_p_state.get("current_hp", 1) <= 0 and not alive_players_after

        if bot_all_fainted:
            battle_over = True
            winner = "사용자"
        elif player_all_fainted:
            battle_over = True
            winner = request.leader_name
        # ──────────────────────────────────────────────────────────────────

        return {
            "messages": messages,
            "battle_over": battle_over,
            "winner": winner,
            "final_user_pokemon": request.user_pokemon,
            "final_bot_pokemon": request.bot_pokemon,
        }
    except Exception as e:
        import traceback
        print("!!! Process Turn Error !!!")
        print(traceback.format_exc()) # 에러 상세 출력
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leader_data")
async def get_leader_data(leader_name: Optional[str] = Query(None)):
    """
    관장별 포켓몬 엔트리 및 대사 데이터를 조회합니다.
    """
    if leader_name:
        roster = ROSTER_MAP.get(leader_name)
        quotes = LEADER_QUOTES.get(leader_name)
        if not roster:
            raise HTTPException(status_code=404, detail=f"Leader '{leader_name}' not found")
        return {"roster": roster, "quotes": quotes}
    
    return {
        "roster_map": ROSTER_MAP,
        "leader_quotes": LEADER_QUOTES
    }


# ── 요청 모델 ─────────────────────────────────────────────────────────────────

class StartBattleRequest(BaseModel):
    leader_name: str = "웅이"

class BotMoveRequest(BaseModel):
    bot_pokemon: Dict[str, Any]      # 현재 출전 중인 봇 포켓몬 상태
    player_pokemon: Dict[str, Any]   # 현재 출전 중인 플레이어 포켓몬 상태
    bot_party: List[Dict[str, Any]]  # 현재 HP가 반영된 전체 봇 파티
    strategy: str = "llm"            # 'random' | 'llm'


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post("/start")
async def start_battle(request: StartBattleRequest):
    """
    배틀을 초기화합니다.
    - 관장 엔트리에서 랜덤 3마리를 선택합니다.
    - BotPokemonDB로 포켓몬 데이터(스탯, 기술 등)를 조회합니다.
    - 첫 턴 봇 행동을 미리 결정하여 함께 반환합니다.

    반환값:
        bot_party:       초기화된 봇 파티 (dict 리스트)
        first_bot_move:  첫 턴 봇 행동
        quotes:          관장 대사 (start / defeat)
    """
    leader_name = request.leader_name
    leader_data = ROSTER_MAP.get(leader_name)
    if not leader_data:
        raise HTTPException(status_code=404, detail=f"Leader '{leader_name}' not found")
    roster = leader_data.get("roster", []) # 실제 포켓몬 리스트 추출

    try:
        # 1. 관장 엔트리에서 랜덤 3마리 선택
        entries = random.sample(roster, min(3, len(roster)))

        # 2. 각 포켓몬 데이터를 Neo4j에서 조회하여 배틀용 dict로 구성
        bot_party = []
        for entry in entries:
            multiplier = 2.0 if (leader_name == "지우" and entry["name"] == "피카츄") else 1.1
            pokemon_dict = load_bot_pokemon(
                pokemon_id=entry["id"],
                name=entry["name"],
                selected_moves=entry["moves"],
                multiplier=multiplier
            )
            bot_party.append(pokemon_dict)

        # 3. 첫 번째 봇 행동 미리 결정
        #    배틀 시작 직후이므로 플레이어 정보가 없어 random 전략 사용
        first_bot_move = decide_action(
            bot_pokemon=bot_party[0],
            player_pokemon={},           # 아직 플레이어 정보 없음
            bot_party=bot_party,
            strategy="random"            # 첫 턴은 상대 정보가 없으므로 항상 random
        )

        leader_data = ROSTER_MAP.get(leader_name, {})
        leader_quotes = leader_data.get("quotes", {"start": "배틀을 시작합시다!", "defeat": "훌륭했습니다!"})
        return {
            "bot_party": bot_party,
            "first_bot_move": first_bot_move,
            "quotes": leader_quotes
        }

    except Exception as e:
        import traceback
        print("!!! Battle Init Error !!!")
        print(traceback.format_exc())  # 에러 전문을 로그에 출력
        raise HTTPException(status_code=500, detail=f"Battle init error: {str(e)}")


@router.post("/decide_bot_move")
async def decide_bot_move(request: BotMoveRequest):
    """
    현재 배틀 상태를 바탕으로 봇의 다음 행동을 결정합니다.
    (frontend의 prepare_bot_move()에 해당)

    - 턴 종료 직후 호출되어 다음 턴의 봇 행동을 미리 계산합니다.
    - 플레이어 입력 전에 호출되므로, 반환된 행동은 프론트에서 pending_bot_move로 저장합니다.

    반환값:
        bot_move: 봇이 다음 턴에 수행할 행동 dict
    """
    try:
        bot_move = decide_action(
            bot_pokemon=request.bot_pokemon,
            player_pokemon=request.player_pokemon,
            bot_party=request.bot_party,
            strategy=request.strategy
        )
        return {"bot_move": bot_move}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot decision error: {str(e)}")
