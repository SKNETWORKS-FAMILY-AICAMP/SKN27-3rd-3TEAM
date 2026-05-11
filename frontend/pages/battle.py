import os
import sys
import random
import streamlit as st
from dotenv import load_dotenv

# 경로 설정 및 모듈 임포트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(frontend_dir)

load_dotenv(os.path.join(root_dir, ".env"))

if frontend_dir not in sys.path:
    sys.path.append(frontend_dir)

# 모듈화된 배틀 기능 임포트
from battle.data import (
    ROSTER, load_battle_data, get_roster_entry, 
    display_name, build_battle_pokemon, PRIORITY_MOVES
)
from battle.engine import resolve_attack, find_player_move, stat_value
from battle.ai import call_llm_for_move
from battle.ui import inject_battle_styles, render_pokemon_status, fmt_player, fmt_bot, fmt_move
from utils.ui import inject_common_ui

# 페이지 설정
st.set_page_config(
    page_title="Battle - Pokemon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)

def reset_battle():
    """배틀 세션 상태 초기화"""
    for key in [
        "battle_player", "battle_bot", "battle_messages", 
        "battle_over", "winner", "turn_count", "hidden_bot_entry"
    ]:
        st.session_state.pop(key, None)

def start_battle(selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types):
    """배틀 시작 및 초기 메시지 설정"""
    reset_battle()
    candidates = [entry for entry in ROSTER if entry["pokemon_id"] != selected_player_entry["pokemon_id"]]
    bot_entry = random.choice(candidates)
    st.session_state.hidden_bot_entry = bot_entry
    st.session_state.battle_player = build_battle_pokemon(
        selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types
    )
    st.session_state.battle_bot = build_battle_pokemon(
        bot_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types
    )
    st.session_state.battle_messages = [
        {
            "role": "assistant",
            "content": (
                "배틀이 시작되었습니다.\n\n"
                f"상대 LLM Bot의 포켓몬은 {fmt_bot(bot_entry['name'])}입니다.\n\n"
                "이제 채팅창에 사용할 기술명을 입력해 주세요."
            ),
        }
    ]
    st.session_state.battle_over = False
    st.session_state.winner = None
    st.session_state.turn_count = 0

def process_turn(player_move, efficacy):
    """한 턴의 배틀 진행 처리"""
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    bot_move, _ = call_llm_for_move(bot, player, efficacy)

    st.session_state.turn_count += 1
    lines = [
        f"Turn {st.session_state.turn_count}",
        f"당신: {fmt_player(player.name)}에게 {fmt_move(player_move['name'])}을(를) 지시했습니다.",
        f"LLM Bot: {fmt_bot(bot.name)}은(는) {fmt_move(bot_move['name'])}을(를) 선택했습니다.",
    ]

    # 우선도 및 스피드에 따른 공격 순서 결정
    player_priority = PRIORITY_MOVES.get(player_move["name"], 0)
    bot_priority = PRIORITY_MOVES.get(bot_move["name"], 0)
    order = [(player, bot, player_move), (bot, player, bot_move)]
    
    if bot_priority > player_priority:
        order.reverse()
    elif bot_priority == player_priority:
        if stat_value(bot, "speed") > stat_value(player, "speed"):
            order.reverse()
        elif stat_value(bot, "speed") == stat_value(player, "speed"):
            random.shuffle(order)

    # 공격 실행
    for attacker, defender, move in order:
        if attacker.current_hp <= 0:
            continue
        lines.append(resolve_attack(attacker, defender, move, efficacy))
        if defender.current_hp <= 0:
            defender_name = fmt_player(defender.name) if defender is player else fmt_bot(defender.name)
            winner_label = "USER" if attacker is player else "LLM"
            lines.append(f"{defender_name}이 쓰러졌습니다.")
            st.session_state.battle_over = True
            st.session_state.winner = winner_label
            lines.append(f"승리: {winner_label}")
            break

    st.session_state.battle_messages.append({"role": "assistant", "content": "\n\n".join(lines)})

def show():
    """배틀 페이지 메인 렌더링 함수"""
    all_pokemon, all_stats, all_types, moves_by_name, pokemon_types, efficacy = load_battle_data()
    inject_battle_styles()

    st.markdown(
        """
        <div class="battle-header">
            <h1>포켓몬 1대1 배틀</h1>
            <p>포켓몬을 고르고 배틀을 시작하세요. 상대는 시작 전까지 비공개이며, 나의 포켓몬에게 채팅창을 통해 지시를 내리세요!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 배틀 시작 전: 포켓몬 선택 화면
    if "battle_player" not in st.session_state:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            selected_player_id = st.selectbox(
                "내 포켓몬 선택",
                [entry["pokemon_id"] for entry in ROSTER],
                format_func=lambda pid: display_name(get_roster_entry(pid)),
            )
            selected_player_entry = get_roster_entry(selected_player_id)
            preview = build_battle_pokemon(selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types)
            render_pokemon_status("PLAYER ENTRY", preview)
            
            st.markdown("<hr style='border: 1px solid rgba(148, 163, 184, .24); margin: 20px 0;'>", unsafe_allow_html=True)
            st.markdown("<div class='secret-card'>LLM BOT<br>???</div>", unsafe_allow_html=True)

            if st.button("배틀 시작", use_container_width=True):
                start_battle(selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types)
                st.rerun()
        return

    # 배틀 진행 중 화면
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    col1, col2 = st.columns([1, 1.2])

    with col1:
        render_pokemon_status("PLAYER", player)
        st.markdown("<hr style='border: 1px solid rgba(148, 163, 184, .24); margin: 20px 0;'>", unsafe_allow_html=True)
        render_pokemon_status("LLM BOT", bot, reveal_details=False)
        
        if st.button("새 배틀 준비", use_container_width=True):
            reset_battle()
            st.rerun()

    with col2:
        # 배틀 메시지 로그 (스크롤 영역)
        with st.container(height=650):
            for message in st.session_state.get("battle_messages", []):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"], unsafe_allow_html=True)

            if st.session_state.get("battle_over"):
                st.info(f"배틀 종료. 승리: {st.session_state.winner}")

        # 채팅 입력창
        if not st.session_state.get("battle_over"):
            prompt = st.chat_input(f"{player.name}에게 지시를 내리세요!")
            if prompt:
                st.session_state.battle_messages.append({"role": "user", "content": prompt})
                player_move = find_player_move(prompt, player)
                if not player_move:
                    st.session_state.battle_messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                "그 기술은 현재 사용할 수 없습니다. 사용 가능한 기술은 "
                                + " / ".join(fmt_move(move["name"]) for move in player.moves)
                                + " 입니다."
                            ),
                        }
                    )
                else:
                    process_turn(player_move, efficacy)
                st.rerun()

if __name__ == "__main__":
    show()
