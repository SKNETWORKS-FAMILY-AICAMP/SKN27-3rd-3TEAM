import os
import time
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

from .ui import (
    render_pokemon_status,
    get_trainer_image_base64,
)
from .utils import prepare_bot_move, process_turn, find_player_action

def display_battle():
    # 배틀 진행 화면
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    leader_name = st.session_state.get("leader_name", "관장")

    # ─── 1. Battle Row (Player vs Bot | Leader) ───
    b_col1, b_col_vs, b_col2, b_col_img = st.columns([1.2, 0.2, 1, 0.8])
    
    with b_col1:
        player_placeholder = st.empty()
        with player_placeholder:
            render_pokemon_status("MY POKEMON", player, reveal_details=True)
    
    with b_col_vs:
        st.markdown('<div class="vs-badge">VS</div>', unsafe_allow_html=True)
        
    with b_col2:
        bot_placeholder = st.empty()
        with bot_placeholder:
            render_pokemon_status(f"BOT ({leader_name})", bot, reveal_details=False)
    
    with b_col_img:
        trainer_img = get_trainer_image_base64(leader_name)
        if trainer_img:
            st.markdown(f"""
                <div class="leader-portrait-card">
                    <img src="{trainer_img}" class="leader-portrait-img">
                    <div style="color: #f8fafc; font-weight: 900; margin-top: 10px; font-size: 1.1rem;">{leader_name}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── 3. Interaction Row (History | Input) ───
    i_col1, i_col2 = st.columns([1.2, 1])

    with i_col1:
        with st.container(border=True):
            st.markdown('<div class="battle-section-title">BATTLE LOG</div>', unsafe_allow_html=True)
            history_container = st.container(height=420)
            with history_container:
                for message in st.session_state.battle_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"], unsafe_allow_html=True)

    with i_col2:
        with st.container(border=True):
            st.markdown('<div class="battle-section-title">TRAINER COMMAND</div>', unsafe_allow_html=True)

            # 대기 중인 메시지가 있다면 지연을 두고 하나씩 출력
            if "pending_messages" in st.session_state and st.session_state.pending_messages:
                for msg_event in st.session_state.pending_messages:
                    time.sleep(0.8)

                    msg_text = msg_event["message"]
                    p_state = msg_event["player_state"]
                    b_state = msg_event["bot_state"]
                    is_bot_switch = msg_event.get("bot_switch")

                    if not is_bot_switch:
                        player.current_hp = p_state.get("current_hp", player.max_hp)
                        player.attack_stage = p_state.get("attack_stage", 0)
                        player.defense_stage = p_state.get("defense_stage", 0)
                        player.sp_attack_stage = p_state.get("sp_attack_stage", 0)
                        player.sp_defense_stage = p_state.get("sp_defense_stage", 0)
                        player.speed_stage = p_state.get("speed_stage", 0)
                        player.ailment = p_state.get("ailment")
                        player.sleep_turns = p_state.get("sleep_turns", 0)
                        bot.current_hp = b_state.get("current_hp", bot.max_hp)
                        bot.attack_stage = b_state.get("attack_stage", 0)
                        bot.defense_stage = b_state.get("defense_stage", 0)
                        bot.sp_attack_stage = b_state.get("sp_attack_stage", 0)
                        bot.sp_defense_stage = b_state.get("sp_defense_stage", 0)
                        bot.speed_stage = b_state.get("speed_stage", 0)
                        bot.ailment = b_state.get("ailment")
                        bot.sleep_turns = b_state.get("sleep_turns", 0)
                        with player_placeholder:
                            render_pokemon_status("MY POKEMON", player)
                        with bot_placeholder:
                            render_pokemon_status(f"BOT ({leader_name})", bot, reveal_details=False)
                        with history_container:
                            with st.chat_message("assistant"):
                                st.markdown(msg_text, unsafe_allow_html=True)
                        st.session_state.battle_messages.append({"role": "assistant", "content": msg_text})
                    else:
                        player.current_hp = p_state.get("current_hp", player.max_hp)
                        player.attack_stage = p_state.get("attack_stage", 0)
                        player.defense_stage = p_state.get("defense_stage", 0)
                        player.sp_attack_stage = p_state.get("sp_attack_stage", 0)
                        player.sp_defense_stage = p_state.get("sp_defense_stage", 0)
                        player.speed_stage = p_state.get("speed_stage", 0)
                        player.ailment = p_state.get("ailment")
                        player.sleep_turns = p_state.get("sleep_turns", 0)
                        with player_placeholder:
                            render_pokemon_status("MY POKEMON", player)
                        with history_container:
                            with st.chat_message("assistant"):
                                st.markdown(msg_text, unsafe_allow_html=True)
                        st.session_state.battle_messages.append({"role": "assistant", "content": msg_text})
                        time.sleep(0.6)
                        next_idx = msg_event["bot_next_index"]
                        st.session_state.battle_bot = st.session_state.bot_party[next_idx]
                        bot = st.session_state.battle_bot
                        with bot_placeholder:
                            render_pokemon_status(f"BOT ({leader_name})", bot, reveal_details=False)

                st.session_state.pending_messages = []
                battle_continues = True
                battle_over_from_api = st.session_state.pop("pending_battle_over", False)
                winner_from_api = st.session_state.pop("pending_winner", None)
                if battle_over_from_api:
                    st.session_state.battle_over = True
                    st.session_state.winner = winner_from_api
                    battle_continues = False
                elif player.current_hp <= 0:
                    alive_players = [pp for pp in st.session_state.player_party if pp.current_hp > 0]
                    if alive_players:
                        st.session_state.waiting_for_switch = True
                    else:
                        st.session_state.battle_over = True
                        st.session_state.winner = st.session_state.get("leader_name", "관장")
                        battle_continues = False
                if battle_continues and not st.session_state.get("waiting_for_switch", False):
                    prepare_bot_move()
                st.rerun()

            if st.session_state.get("battle_over", False):
                winner = st.session_state.winner
                if winner == "사용자":
                    quotes = st.session_state.get("leader_quotes", {"defeat": "훌륭한 승리였습니다!"})
                    st.markdown(f"""
                        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                            <div style="color: #10b981; font-weight: 900; font-size: 1.2rem; margin-bottom: 10px;">🏆 배틀 승리!</div>
                            <div style="color: #e2e8f0; font-style: italic; font-size: 1rem;">{st.session_state.leader_name}: "{quotes['defeat']}"</div>
                            <div style="color: #e2e8f0; font-size: 0.9rem; margin-top: 10px;">{st.session_state.leader_name}과(와)의 승부에서 이겼다!</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if not st.session_state.get("victory_logged", False):
                        user = st.session_state.get("user")
                        if user and user.get("db_id"):
                            try:
                                payload = {
                                    "user_id": user["db_id"],
                                    "game_type": "gym_battle",
                                    "is_correct": True,
                                    "log_data": f'{{"leader": "{st.session_state.leader_name}"}}'
                                }
                                requests.post(f"{BACKEND_URL}/api/v1/users/game-log", json=payload, timeout=3)
                            except Exception as e:
                                print(f"Error logging victory: {e}")
                        st.session_state.victory_logged = True
                    if st.button("메인 메뉴로 돌아가기", use_container_width=True):
                        st.session_state.battle_stage = "menu"
                        st.session_state.battle_over = False
                        st.session_state.victory_logged = False
                        st.rerun()
                else:
                    st.error("주인공에게는 싸울 수 있는 포켓몬이 없다! 주인공은 눈앞이 캄캄해졌다!")
                    if st.button("메인 메뉴로 돌아가기", use_container_width=True):
                        st.session_state.battle_stage = "menu"
                        st.session_state.battle_over = False
                        st.rerun()

            if not st.session_state.get("battle_over", False):
                # ----------------- 행동 UI -----------------
                if st.session_state.get("waiting_for_switch"):
                    st.warning("포켓몬이 쓰러졌습니다! 교체할 포켓몬을 선택해주세요.")
                    party_cols = st.columns(len(st.session_state.player_party))
                    for i, p_obj in enumerate(st.session_state.player_party):
                        with party_cols[i]:
                            disabled = (p_obj.current_hp <= 0 or p_obj.id == player.id)
                            label = f"{p_obj.name} (HP {p_obj.current_hp})"
                            if st.button(label, disabled=disabled, use_container_width=True, key=f"force_switch_{i}"):
                                new_player = st.session_state.player_party[i]
                                current_bot = st.session_state.battle_bot
                                switch_msg = f"가라! {new_player.name}!"
                                st.session_state.pending_messages = [{
                                    "message": switch_msg,
                                    "player_state": {
                                        "current_hp": new_player.current_hp,
                                        "attack_stage": new_player.attack_stage,
                                        "defense_stage": new_player.defense_stage,
                                        "sp_attack_stage": new_player.sp_attack_stage,
                                        "sp_defense_stage": new_player.sp_defense_stage,
                                        "speed_stage": new_player.speed_stage,
                                        "ailment": new_player.ailment,
                                        "sleep_turns": new_player.sleep_turns,
                                    },
                                    "bot_state": {
                                        "current_hp": current_bot.current_hp,
                                        "attack_stage": current_bot.attack_stage,
                                        "defense_stage": current_bot.defense_stage,
                                        "sp_attack_stage": current_bot.sp_attack_stage,
                                        "sp_defense_stage": current_bot.sp_defense_stage,
                                        "speed_stage": current_bot.speed_stage,
                                        "ailment": current_bot.ailment,
                                        "sleep_turns": current_bot.sleep_turns,
                                    },
                                }]
                                st.session_state.battle_player = new_player
                                st.session_state.waiting_for_switch = False
                                st.session_state.battle_messages.append({"role": "user", "content": switch_msg})
                                prepare_bot_move()
                                st.rerun()
                else:
                    st.markdown('<div class="battle-divider"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="battle-section-title">무엇을 할까?</div>', unsafe_allow_html=True)
                    action_choice = st.radio("행동 선택", ["기술 사용", "포켓몬 교체"], horizontal=True, label_visibility="collapsed")

                    if action_choice == "기술 사용":
                        prompt = st.chat_input(f"{player.name}에게 명령을 내리세요!")
                        if prompt:
                            with history_container:
                                st.session_state.battle_messages.append({"role": "user", "content": prompt})
                                player_move = find_player_action(prompt, player, st.session_state.player_party)
                                if not player_move:
                                    st.session_state.battle_messages.append({
                                        "role": "assistant",
                                        "content": f"사용 불가능한 명령입니다. 가능 기술: {' / '.join(m['name'] for m in player.moves)}"
                                    })
                                elif player_move.get("category") == "switch":
                                    st.session_state.battle_messages.append({
                                        "role": "assistant",
                                        "content": "포켓몬 교체는 '포켓몬 교체' 메뉴를 이용해주세요."
                                    })
                                else:
                                    process_turn(player_move)
                            st.rerun()

                    elif action_choice == "포켓몬 교체":
                        st.write("교체할 포켓몬을 선택하세요.")
                        party_cols = st.columns(len(st.session_state.player_party))
                        for i, p_obj in enumerate(st.session_state.player_party):
                            with party_cols[i]:
                                disabled = (p_obj.current_hp <= 0 or p_obj.id == player.id)
                                label = f"{p_obj.name} (HP {p_obj.current_hp})"
                                if st.button(label, disabled=disabled, use_container_width=True, key=f"switch_{i}"):
                                    switch_action = {"name": f"{p_obj.name}(으)로 교체", "category": "switch", "target_index": i, "priority": 6}
                                    st.session_state.battle_messages.append({"role": "user", "content": f"{p_obj.name}(으)로 교체!"})
                                    process_turn(switch_action)
                                    st.rerun()

                    st.markdown('<div class="battle-divider"></div>', unsafe_allow_html=True)
                    if st.button("🚫 배틀 중단", use_container_width=True):
                        st.session_state.battle_started = False
                        st.session_state.battle_stage = "menu"
                        st.rerun()