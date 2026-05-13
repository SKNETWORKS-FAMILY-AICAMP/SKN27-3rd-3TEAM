import re
import time
import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"

from battle.ui import inject_battle_styles, render_pokemon_status, fmt_player, fmt_bot, fmt_move
from utils.ui import inject_common_ui
from battle.pokemon import PokemonDB
from battle.utils import BattlePokemon
from battle.movetree import run_battle_logic
from battle.trainer_bot import BattleBot
from battle.trainerbot import ROSTER_MAP
from dataclasses import asdict

# 페이지 설정
st.set_page_config(
    page_title="Battle - Pokemon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)
inject_battle_styles()

# DB 연결
db = PokemonDB()

def start_custom_battle(player_team_data, leader_name="웅이"):
    """
    DB 데이터를 기반으로 BattlePokemon 객체를 생성하고 배틀을 초기화합니다.
    
    - player_team_data: 파티 리스트 [{"id", "name", "moves"}, ...]
    """
    with st.spinner("배틀 데이터를 준비 중..."):
        # 1. 플레이어 파티 구성
        player_party = []
        for p_custom in player_team_data:
            pokemon_obj = BattlePokemon(
                id=p_custom["id"],
                name=p_custom["name"],
                selected_moves=p_custom["moves"]
            )
            player_party.append(pokemon_obj)
            
        st.session_state.player_party = player_party
        st.session_state.battle_player = player_party[0] # 선봉 포켓몬

        # 2. 봇 파티 구성 (관장의 전체 엔트리 중 랜덤 3마리 선택)
        bot_party = BattleBot.initialize(leader_name)

        st.session_state.bot_party = bot_party
        st.session_state.battle_bot = bot_party[0] # 관장 봇의 선봉 포켓몬
        st.session_state.leader_name = leader_name

        # 3. 배틀 공통 데이터 및 메시지 초기화
        st.session_state.efficacy = db.get_type_efficacy()
        st.session_state.battle_messages = [
            {"role": "assistant", "content": f"배틀이 시작되었습니다! 첫 상대는 {fmt_bot(bot_party[0].name)}입니다. 어떤 기술을 사용하시겠습니까?"}
        ]
        st.session_state.battle_started = True
        st.session_state.battle_over = False
        st.session_state.turn_count = 0

def find_player_action(text: str, player: BattlePokemon, player_party: list):
    normalized = re.sub(r"\s+", "", text.strip().lower())
    
    # 교체 시도 확인
    for idx, p in enumerate(player_party):
        if p.id == player.id or p.current_hp <= 0: continue
        p_name = re.sub(r"\s+", "", p.name.lower())
        if p_name in normalized:
            return {"name": f"{p.name}(으)로 교체", "category": "switch", "target_index": idx, "priority": 6}

    # 기술 시도 확인
    for move in player.moves:
        move_name = re.sub(r"\s+", "", move["name"].lower())
        if normalized == move_name or move_name in normalized:
            return move
    return None

def process_turn(player_move):
    """
    [한 턴의 배틀 진행 처리]
    """
    # 1. 플레이어 교체 처리 (턴 소모)
    if player_move.get("category") == "switch":
        target_idx = player_move["target_index"]
        st.session_state.battle_player = st.session_state.player_party[target_idx]
        
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    bot_party = st.session_state.bot_party
    
    # =========================== 봇의 행동 결정 로직 =============================
    # 봇의 전략 결정 (세션 상태에서 가져오거나 기본값 'random' 사용)
    bot_strategy = st.session_state.get("bot_strategy", "random")
    trainer_bot = BattleBot(leader_name=st.session_state.leader_name)
    bot_move = trainer_bot.decide_action(strategy=bot_strategy)
    bot = st.session_state.battle_bot  # 교체되었을 수 있으므로 갱신
    # ===============================================================================

    # 객체를 딕셔너리로 변환
    player_dict = asdict(player)
    bot_dict = asdict(bot)
    
    # 배틀 로직 실행
    messages = run_battle_logic(player_dict, bot_dict, player_move, bot_move)
    
    # 최종 상태 추출
    final_p_state = messages[-1]["player_state"]
    final_b_state = messages[-1]["bot_state"]
    
    # 사망 시 봇 강제 교체 메시지만 미리 생성 (UI 루프에서 처리하기 위함)
    if final_b_state.get("current_hp", 100) <= 0:
        bot_party = st.session_state.bot_party
        alive_bots = [bp for bp in bot_party if bp.id != bot.id and bp.current_hp > 0]
        if alive_bots:
            next_bot = alive_bots[0]
            messages.append({
                "message": f"{st.session_state.leader_name}은(는) {next_bot.name}을(를) 내보냈다!",
                "player_state": final_p_state,
                "bot_state": asdict(next_bot),
                "bot_switch": True,
                "bot_next_index": bot_party.index(next_bot)
            })
            
    st.session_state.pending_messages = messages

def show():
    if "player_team" not in st.session_state:
        st.session_state.player_team = []
    if "battle_stage" not in st.session_state:
        st.session_state.battle_stage = "menu"

    gym_leaders = ["웅이", "이슬이", "아이리스", "민화", "풍란", "채두", "순무", "지우", "N"]

    if st.session_state.battle_stage == "menu":
        st.markdown(
            """
            <div class="battle-header" style="text-align:center; padding: 40px 0;">
                <h1>포켓몬 배틀 아레나</h1>
                <p>나만의 팀을 구성하거나 즉시 배틀을 시작하세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.subheader("관장 선택")
        selected_leader = st.selectbox("대결할 관장을 선택하세요", options=gym_leaders, index=0)
        st.session_state.selected_leader = selected_leader
        
        leader_roster = ROSTER_MAP.get(selected_leader, [])
        if leader_roster:
            st.caption(f"**{selected_leader}의 엔트리:**")
            cols = st.columns(len(leader_roster))
            for idx, p in enumerate(leader_roster):
                pokemon_data = db.get_pokemon_data(p['id'])
                with cols[idx]:
                    img_url = pokemon_data['image_url']
                    st.image(img_url, use_container_width=True)
                    st.markdown(f"<div style='text-align: center; font-size: 0.85rem; font-weight: 700; color: #cbd5e1;'>{p['name']}</div>", unsafe_allow_html=True)
                    
        st.markdown("<hr>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛠️ 팀 구성하기", use_container_width=True, type="primary"):
                user = st.session_state.get("user")
                if user and user.get("db_id"):
                    try:
                        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", timeout=3)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data and "team_data" in data:
                                st.session_state.player_team = data["team_data"]
                    except:
                        pass # 불러오기 실패해도 빈 팀으로 시작
                st.session_state.battle_stage = "teambuilding"
                st.rerun()
        with col2:
            if st.button("⚔️ 배틀 시작하기", use_container_width=True, type="secondary"):
                user = st.session_state.get("user")
                if user and user.get("db_id"):
                    try:
                        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", timeout=3)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data and "team_data" in data and data["team_data"]:
                                st.session_state.player_team = data["team_data"]
                            else:
                                st.warning("저장된 팀이 없습니다. '팀 구성하기'를 통해 팀을 먼저 구성해주세요.")
                                return
                        else:
                            st.warning("저장된 팀을 불러올 수 없습니다. 팀을 먼저 구성해주세요.")
                            return
                    except Exception as e:
                        st.error(f"서버와 통신할 수 없습니다: {e}")
                        return
                
                if len(st.session_state.player_team) > 0:
                    st.session_state.battle_stage = "battle"
                    start_custom_battle(st.session_state.player_team, leader_name=st.session_state.selected_leader)
                    db.close()
                    st.rerun()
                else:
                    st.warning("자신의 포켓몬을 선택해주세요!")

    elif st.session_state.battle_stage == "teambuilding":
        st.markdown(
            """
            <div class="battle-header">
                <h1>포켓몬 검색 및 팀 구성</h1>
                <p>원하는 포켓몬을 검색하고, 4가지 기술을 선택하여 배틀을 준비하세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pokemon_list = db.get_all_pokemon_names()
        pokemon_options = {p['name']: p['id'] for p in pokemon_list}
        
        col1, col2 = st.columns([1, 1.2])

        with col1:
            st.markdown("<hr>", unsafe_allow_html=True)
            if "selected_leader" not in st.session_state:
                st.session_state.selected_leader = "웅이"
            st.info(f"현재 선택된 상대: **{st.session_state.selected_leader}**")

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("포켓몬 선택")
            selected_name = st.selectbox(
                "포켓몬 이름을 검색하세요",
                options=list(pokemon_options.keys()),
                index=None,                placeholder="포켓몬 이름 입력..."
            )

            st.markdown("<hr>", unsafe_allow_html=True)
            if selected_name:
                pokemon_id = pokemon_options[selected_name]
                if "selected_pokemon_data" not in st.session_state or st.session_state.get("last_selected_id") != pokemon_id:
                    st.session_state.selected_pokemon_data = db.get_pokemon_data(pokemon_id)
                    st.session_state.last_selected_id = pokemon_id
                    st.session_state.selected_moves = []

                pokemon_data = st.session_state.selected_pokemon_data
                preview = BattlePokemon(
                    id=pokemon_data['id'], name=pokemon_data['name'], selected_moves=st.session_state.selected_moves
                )
                render_pokemon_status("PLAYER PREVIEW", preview, show_moves=False)

        with col2:
            st.subheader(f"내 파티 ({len(st.session_state.player_team)}/3)")
            if st.session_state.player_team:
                team_cols = st.columns(len(st.session_state.player_team))
                for i, pt in enumerate(st.session_state.player_team):
                    pokemon_data = db.get_pokemon_data(pt['id'])
                    with team_cols[i]:
                        img_url = pokemon_data['image_url']
                        st.image(img_url, use_container_width=True)
                        st.markdown(f"<div style='text-align: center; font-size: 0.8rem; margin-bottom: 8px;'>{pt['name']}</div>", unsafe_allow_html=True)
                        if st.button("❌ 제외", key=f"remove_pt_{i}_{pt['name']}", use_container_width=True):
                            st.session_state.player_team.pop(i)
                            st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)

            if selected_name:
                st.subheader("기술 선택")
                pokemon_data = st.session_state.selected_pokemon_data
                if "selected_moves" not in st.session_state:
                    st.session_state.selected_moves = []
                
                selected_move_names = st.session_state.selected_moves
                
                st.write(f"**선택된 기술 ({len(selected_move_names)}/4)**")
                if selected_move_names:
                    cols = st.columns(4)
                    for i in range(4):
                        if i < len(selected_move_names):
                            cols[i].info(selected_move_names[i])
                        else:
                            cols[i].write("Empty")
                
                st.write("---")
                move_cols = st.columns(4)
                for i, move in enumerate(pokemon_data['moves']):
                    m_name = move['name']
                    is_selected = m_name in selected_move_names
                    b_type = "primary" if is_selected else "secondary"
                    if move_cols[i % 4].button(m_name, key=f"mv_{m_name}", use_container_width=True, type=b_type):
                        if is_selected:
                            st.session_state.selected_moves.remove(m_name)
                        elif len(st.session_state.selected_moves) < 4:
                            st.session_state.selected_moves.append(m_name)
                        st.rerun()

                st.write("---")
                if len(selected_move_names) == 4:
                    st.success("모든 기술 선택 완료!")
                    if len(st.session_state.player_team) < 3:
                        if st.button("➕ 엔트리에 추가하기", use_container_width=True, type="secondary"):
                            four_moves = [m for m in pokemon_data['moves'] if m['name'] in selected_move_names]
                            player_custom = {"id": pokemon_data['id'], "name": pokemon_data['name'], "moves": four_moves}
                            st.session_state.player_team.append(player_custom)
                            st.session_state.selected_moves = []
                            st.session_state.last_selected_id = None
                            st.rerun()
                    else:
                        st.warning("파티가 가득 찼습니다! (최대 3마리)")
                else:
                    st.info(f"기술을 {4 - len(selected_move_names)}개 더 선택해주세요.")

        with col2:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("현재 나의 엔트리")
            if not st.session_state.player_team:
                st.info("선택된 포켓몬이 없습니다. 왼쪽에서 검색하여 추가해주세요.")
            else:
                party_cols = st.columns(3)
                for idx, p in enumerate(st.session_state.player_team):
                    with party_cols[idx]:
                        p_data = db.get_pokemon_data(p['id'])
                        st.image(p_data['image_url'], use_container_width=True)
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{p['name']}</div>", unsafe_allow_html=True)
                        moves_text = ", ".join([m['name'] for m in p['moves']])
                        st.caption(f"기술: {moves_text}")
                
                if st.button("🗑️ 엔트리 전체 비우기", use_container_width=True):
                    st.session_state.player_team = []
                    st.rerun()

            if len(st.session_state.player_team) > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 포켓몬 선택 완료 및 배틀로 이동", use_container_width=True, type="primary"):
                    user = st.session_state.get("user")
                    if user and user.get("db_id"):
                        try:
                            payload = {"team_data": st.session_state.player_team}
                            resp = requests.post(f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", json=payload, timeout=3)
                            if resp.status_code == 200:
                                st.success("팀이 성공적으로 저장되었습니다!")
                            else:
                                st.warning("팀 저장에 실패했습니다.")
                        except Exception as e:
                            st.warning(f"팀을 저장하는 중 오류가 발생했습니다: {e}")
                    
                    st.session_state.battle_stage = "battle"
                    start_custom_battle(st.session_state.player_team, leader_name=st.session_state.selected_leader)
                    db.close()
                    st.rerun()
                
                if st.button("⬅️ 메뉴로 돌아가기", use_container_width=True):
                    st.session_state.battle_stage = "menu"
                    st.rerun()
    
    elif st.session_state.battle_stage == "battle":
        # 배틀 진행 화면 (battle.py 로직과 유사)
        player = st.session_state.battle_player
        bot = st.session_state.battle_bot
        col1, col2 = st.columns([1, 1.2])

        with col1:
            player_placeholder = st.empty()
            st.markdown("<hr>", unsafe_allow_html=True)
            bot_placeholder = st.empty()
            
            with player_placeholder:
                render_pokemon_status("PLAYER", player, reveal_details=True)
            with bot_placeholder:
                render_pokemon_status("LLM BOT", bot, reveal_details=False)
            
            if st.button("배틀 중단 및 다시 선택", use_container_width=True):
                st.session_state.battle_started = False
                st.rerun()

        with col2:
            with st.container(height=600):
                for message in st.session_state.battle_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"], unsafe_allow_html=True)
                        
                # 대기 중인 메시지가 있다면 지연을 두고 하나씩 출력
                if "pending_messages" in st.session_state and st.session_state.pending_messages:
                    for msg_event in st.session_state.pending_messages:
                        time.sleep(0.8) # 0.8초 딜레이
                        
                        # 1. 상태 업데이트 및 동기화
                        msg_text = msg_event["message"]
                        p_state = msg_event["player_state"]
                        b_state = msg_event["bot_state"]
                        
                        if msg_event.get("bot_switch"):
                            next_idx = msg_event["bot_next_index"]
                            st.session_state.battle_bot = st.session_state.bot_party[next_idx]
                            bot = st.session_state.battle_bot
                        
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
                        
                        # 2. UI 갱신
                        with player_placeholder:
                            render_pokemon_status("PLAYER", player)
                        with bot_placeholder:
                            render_pokemon_status("LLM BOT", bot, reveal_details=False)
                            
                        # 3. 메시지 출력
                        with st.chat_message("assistant"):
                            st.markdown(msg_text, unsafe_allow_html=True)
                        st.session_state.battle_messages.append({"role": "assistant", "content": msg_text})
                        
                    st.session_state.pending_messages = []
                    
                    # 애니메이션 종료 후 상태 판별 (현재 player, bot은 최종 상태임)
                    if bot.current_hp <= 0:
                        alive_bots = [bp for bp in st.session_state.bot_party if bp.current_hp > 0]
                        if not alive_bots:
                            st.session_state.battle_over = True
                            st.session_state.winner = "사용자"
                            
                    if player.current_hp <= 0:
                        alive_players = [pp for pp in st.session_state.player_party if pp.current_hp > 0]
                        if alive_players:
                            st.session_state.waiting_for_switch = True
                        else:
                            st.session_state.battle_over = True
                            st.session_state.winner = st.session_state.get("leader_name", "관장")
                            
                    st.rerun()

                if st.session_state.get("battle_over", False):
                    winner = st.session_state.winner
                    if winner == "사용자":
                        st.success(f"체육관 관장 {st.session_state.leader_name}과(와)의 승부에서 이겼다!")
                        # 승리 기록 DB 저장
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
                        st.error(f"주인공에게는 싸울 수 있는 포켓몬이 없다! 주인공은 눈앞이 캄캄해졌다!")
                        if st.button("메인 메뉴로 돌아가기", use_container_width=True):
                            st.session_state.battle_stage = "menu"
                            st.session_state.battle_over = False
                            st.rerun()

            if not st.session_state.battle_over:
                # ----------------- 행동 UI -----------------
                if st.session_state.get("waiting_for_switch"):
                    st.warning("포켓몬이 쓰러졌습니다! 교체할 포켓몬을 선택해주세요.")
                    party_cols = st.columns(len(st.session_state.player_party))
                    for i, p_obj in enumerate(st.session_state.player_party):
                        with party_cols[i]:
                            disabled = (p_obj.current_hp <= 0 or p_obj.id == player.id)
                            label = f"{p_obj.name} (HP {p_obj.current_hp})"
                            if st.button(label, disabled=disabled, use_container_width=True, key=f"force_switch_{i}"):
                                st.session_state.battle_player = st.session_state.player_party[i]
                                st.session_state.waiting_for_switch = False
                                
                                new_player = st.session_state.battle_player
                                st.session_state.battle_messages.append({
                                    "role": "assistant", 
                                    "content": f"가라! {new_player.name}!"
                                })
                                st.rerun()
                else:
                    st.write("---")
                    st.subheader("무엇을 할까?")
                    
                    action_choice = st.radio("행동 선택", ["기술 사용", "포켓몬 교체"], horizontal=True, label_visibility="collapsed")
                    
                    if action_choice == "기술 사용":
                        prompt = st.chat_input(f"{player.name}에게 명령을 내리세요!")
                        if prompt:
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
                        st.write("교체할 포켓몬을 선택하세요 (교체 시 턴이 소모되며, 우선도가 가장 높습니다).")
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

if __name__ == "__main__":
    show()
