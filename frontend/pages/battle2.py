import streamlit as st
import random
import time
from typing import List, Dict
from battle.ui import inject_battle_styles, render_pokemon_status, fmt_player, fmt_bot, fmt_move
from utils.ui import inject_common_ui
from battle.pokemon import PokemonDB
from battle.data import BattlePokemon
from battle.movetree import process_turn as run_battle_logic
import re
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

def start_custom_battle(player_custom_data, leader_name="웅이"):
    """DB 데이터를 기반으로 BattlePokemon 객체를 생성하고 배틀을 초기화합니다."""
    with st.spinner("배틀 데이터를 준비 중..."):
        # 1. 플레이어 포켓몬 데이터 구성
        p_data = db.get_pokemon_data(player_custom_data["id"])
        max_hp = p_data['stats']['hp'] * 2
        st.session_state.battle_player = BattlePokemon(
            id=p_data['id'],
            name=p_data['name'],
            image_url=p_data['image_url'],
            types=p_data['types'],
            type_names=p_data['type_names'],
            stats=p_data['stats'],
            moves=player_custom_data["moves"], # 사용자가 선택한 4개 기술
            max_hp=max_hp,
            current_hp=max_hp
        )

        # 2. 봇 포켓몬(관장) 랜덤 선택 및 데이터 구성
        from battle.trainerbot import get_random_gym_leader_pokemon
        
        bot_entry = get_random_gym_leader_pokemon(leader_name)
        b_data = db.get_pokemon_data(bot_entry['id'])
        
        # 봇은 관장 엔트리에 지정된 기술만 사용
        bot_moves = [m for m in b_data['moves'] if m['name'] in bot_entry['moves']]
        # 예외 처리: DB에 해당 기술이 없어서 빈 리스트가 될 경우 대비
        if not bot_moves:
            bot_moves = random.sample(b_data['moves'], min(4, len(b_data['moves'])))
        elif len(bot_moves) > 4:
            bot_moves = random.sample(bot_moves, 4)
            
        b_max_hp = b_data['stats']['hp'] * 2
        
        st.session_state.battle_bot = BattlePokemon(
            id=b_data['id'],
            name=b_data['name'],
            image_url=b_data['image_url'],
            types=b_data['types'],
            type_names=b_data['type_names'],
            stats=b_data['stats'],
            moves=bot_moves,
            max_hp=b_max_hp,
            current_hp=b_max_hp
        )

        # 3. 배틀 공통 데이터 및 메시지 초기화
        st.session_state.efficacy = db.get_type_efficacy()
        st.session_state.battle_messages = [
            {"role": "assistant", "content": f"배틀이 시작되었습니다! 상대는 {fmt_bot(b_data['name'])}입니다. 어떤 기술을 사용하시겠습니까?"}
        ]
        st.session_state.battle_started = True
        st.session_state.battle_over = False
        st.session_state.turn_count = 0

def find_player_move(text: str, player: BattlePokemon):
    normalized = re.sub(r"\s+", "", text.strip().lower())
    for move in player.moves:
        move_name = re.sub(r"\s+", "", move["name"].lower())
        if normalized == move_name or move_name in normalized:
            return move
    return None

def process_turn(player_move):
    """
    [한 턴의 배틀 진행 처리]
    """
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    
    # 봇의 기술 랜덤 선택
    bot_move = random.choice(bot.moves)
    
    # 객체를 딕셔너리로 변환 (MoveProcessor가 딕셔너리 수정을 전제로 함)
    player_dict = asdict(player)
    bot_dict = asdict(bot)
    
    # 배틀 로직 실행 (movetree.py에서 가져온 함수)
    messages = run_battle_logic(player_dict, bot_dict, player_move, bot_move)
    
    # 최종 승패 판별을 위해 마지막 상태 확인
    final_p_state = messages[-1]["player_state"]
    final_b_state = messages[-1]["bot_state"]
    
    if final_b_state.get("current_hp", 100) <= 0:
        st.session_state.battle_over = True
        st.session_state.winner = player.name
    elif final_p_state.get("current_hp", 100) <= 0:
        st.session_state.battle_over = True
        st.session_state.winner = bot.name
        
    st.session_state.pending_messages = messages

def show():
    # 배틀이 시작되지 않았으면 선택 화면 표시
    if not st.session_state.get("battle_started", False):
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
            st.subheader("관장 선택")
            gym_leaders = ["웅이", "이슬이", "아이리스", "민화", "풍란", "채두", "순무", "비주기", "N"]
            selected_leader = st.selectbox("대결할 관장을 선택하세요", options=gym_leaders, index=0)

            
            st.subheader("포켓몬 선택")
            selected_name = st.selectbox(
                "포켓몬 이름을 검색하세요",
                options=list(pokemon_options.keys()),
                index=None,
                placeholder="포켓몬 이름 입력..."
            )

            
            
            st.markdown("<hr>", unsafe_allow_html=True)
            if selected_name:
                pokemon_id = pokemon_options[selected_name]
                if "selected_pokemon_data" not in st.session_state or st.session_state.get("last_selected_id") != pokemon_id:
                    st.session_state.selected_pokemon_data = db.get_pokemon_data(pokemon_id)
                    st.session_state.last_selected_id = pokemon_id
                    st.session_state.selected_moves = []

                pokemon_data = st.session_state.selected_pokemon_data
                max_hp = pokemon_data['stats']['hp'] * 2
                preview = BattlePokemon(
                    id=pokemon_data['id'], name=pokemon_data['name'], image_url=pokemon_data['image_url'],
                    types=pokemon_data['types'], type_names=pokemon_data['type_names'],
                    stats=pokemon_data['stats'], moves=pokemon_data['moves'],
                    max_hp=max_hp, current_hp=max_hp
                )
                render_pokemon_status("PLAYER PREVIEW", preview)

        with col2:
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
                    if st.button("🚀 배틀 시작하기", use_container_width=True, type="primary"):
                        four_moves = [m for m in pokemon_data['moves'] if m['name'] in selected_move_names]
                        player_custom = {"id": pokemon_data['id'], "name": pokemon_data['name'], "moves": four_moves}
                        start_custom_battle(player_custom, leader_name=selected_leader)
                        st.rerun()
                else:
                    st.info(f"기술을 {4 - len(selected_move_names)}개 더 선택해주세요.")
    
    else:
        # 배틀 진행 화면 (battle.py 로직과 유사)
        player = st.session_state.battle_player
        bot = st.session_state.battle_bot
        col1, col2 = st.columns([1, 1.2])

        with col1:
            player_placeholder = st.empty()
            st.markdown("<hr>", unsafe_allow_html=True)
            bot_placeholder = st.empty()
            
            with player_placeholder:
                render_pokemon_status("PLAYER", player)
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
                        
                        player.current_hp = p_state.get("current_hp", player.max_hp)
                        player.attack_stage = p_state.get("attack_stage", 0)
                        player.defense_stage = p_state.get("defense_stage", 0)
                        player.sp_attack_stage = p_state.get("sp_attack_stage", 0)
                        player.sp_defense_stage = p_state.get("sp_defense_stage", 0)
                        player.speed_stage = p_state.get("speed_stage", 0)
                        if hasattr(player, 'ailment'): player.ailment = p_state.get("ailment")

                        bot.current_hp = b_state.get("current_hp", bot.max_hp)
                        bot.attack_stage = b_state.get("attack_stage", 0)
                        bot.defense_stage = b_state.get("defense_stage", 0)
                        bot.sp_attack_stage = b_state.get("sp_attack_stage", 0)
                        bot.sp_defense_stage = b_state.get("sp_defense_stage", 0)
                        bot.speed_stage = b_state.get("speed_stage", 0)
                        if hasattr(bot, 'ailment'): bot.ailment = b_state.get("ailment")
                        
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
                    st.rerun()

                if st.session_state.get("battle_over", False):
                    st.info(f"배틀 종료. 승리: {st.session_state.winner}")

            if not st.session_state.battle_over:
                prompt = st.chat_input(f"{player.name}에게 명령을 내리세요!")
                if prompt:
                    st.session_state.battle_messages.append({"role": "user", "content": prompt})
                    player_move = find_player_move(prompt, player)
                    if not player_move:
                        st.session_state.battle_messages.append({
                            "role": "assistant", "content": f"사용 불가능한 기술입니다. 가능 기술: {' / '.join(m['name'] for m in player.moves)}"
                        })
                    else:
                        process_turn(player_move)
                    st.rerun()

if __name__ == "__main__":
    show()
