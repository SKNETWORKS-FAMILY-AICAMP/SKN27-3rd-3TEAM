import re
import time
import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"

from battle.ui import inject_battle_styles, render_pokemon_status, fmt_player, fmt_bot, fmt_move, get_trainer_image_base64, GYM_NAME_MAP, get_gym_bg_base64
from utils.ui import inject_common_ui
from battle.pokemon import PokemonDB
from battle.utils import BattlePokemon
from battle.movetree import run_battle_logic
from battle.trainer_bot import BattleBot
from battle.trainerbot import ROSTER_MAP
from dataclasses import asdict

LEADER_QUOTES = {
    "웅이": {
        "start": "나의 굳은 의지는 내 포켓몬에게서도 드러나지! 단단하고 참을성이 강해!",
        "defeat": "나의 바위보다 너의 의지가 더욱 단단했구나... 훌륭한 배틀이었다!"
    },
    "이슬이": {
        "start": "너! 너는 포켓몬을 키울 때 너만의 방침이 있니? 나의 방침은 말이지.. 물타입 포켓몬으로 공격하고 공격하고 ..또 공격하는 거야!",
        "defeat": "정말 대단해! 나의 맹공격을 전부 견뎌내다니... 인정할게, 네가 더 강해!"
    },
    "순무": {
        "start": "불꽃은 위를 향해 타오른다! 우리도 위를 노리는 거다!",
        "defeat": "완전히 불태웠다...! 너의 가능성은 그 이상으로 높이 타오르고 있군!"
    },
    "민화": {
        "start": "당신처럼 강한 분이 찾아오시는 것만으로도 자극이 된답니다.",
        "defeat": "어머나... 이렇게 질 줄은 몰랐네요. 당신의 실력은 활짝 핀 꽃처럼 훌륭했어요."
    },
    "풍란": {
        "start": "자, 그럼 나와 함께 즐거운 것을 하자!",
        "defeat": "앗, 추락해버렸다! 하지만 너와의 배틀, 최고로 즐거운 비행이었어!"
    },
    "채두": {
        "start": "당신이 과연 어떤 공격에도 흔들리지 않는 마음을 가졌는지 제가 시험해보겠습니다.",
        "defeat": "훌륭합니다... 조금의 흔들림도 없는 완벽한 호흡, 제가 한 수 배웠습니다."
    },
    "아이리스": {
        "start": "포켓몬리그 챔피언 아이리스! 당신을 이기겠습니다!",
        "defeat": "정말 분해라! 하지만 너와 네 포켓몬의 유대감은 진짜배기구나! 인정할게!"
    },
    "지우": {
        "start": "너로 정했다!!",
        "defeat": "엄청난 배틀이었어! 우리들의 전력이 통하지 않다니, 넌 정말 강하구나!"
    },
    "N": {
        "start": "나에게는 미래가 보인다!!! 반드시 이긴다!!!",
        "defeat": "네가 바라는 포켓몬과의 세계... 얼마나 사랑으로 넘치게 될지 나도 기대하고 있겠어. 언젠가... 몬스터볼 같은 게 없어도 포켓몬과 사람의 관계가 서로 신뢰하고 도와주는... 그런 세상으로 만들 거다."
    }
}

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
        st.session_state.battle_messages = []
        
        # 첫 인사 메시지 (관장 대사 포함)
        quotes = LEADER_QUOTES.get(leader_name, {"start": "배틀을 시작합시다!"})
        first_content = (
            f"<div style='font-style: italic; color: #94a3b8; margin-bottom: 10px;'>{leader_name}: \"{quotes['start']}\"</div>"
        )
        st.session_state.battle_messages = [
            {"role": "assistant", "content": first_content}
        ]
        
        st.session_state.battle_started = True
        st.session_state.battle_over = False
        st.session_state.turn_count = 0
        
        # 4. 첫 턴의 봇 행동 미리 결정 (배틀 시작 직후, 플레이어 입력 대기 중에 계산)
        st.session_state.pending_bot_move = None
        prepare_bot_move()

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

def prepare_bot_move():
    """
    [다음 턴을 위한 봇 행동 사전 결정]
    현재 배틀 상태를 기반으로 봇의 행동을 미리 결정하여 세션에 저장합니다.
    이 함수는 턴 종료 직후 호출되어야 하며, 플레이어 입력과 무관하게 독립적으로 실행됩니다.
    """
    bot_strategy = st.session_state.get("bot_strategy", "llm")
    trainer_bot = BattleBot(leader_name=st.session_state.leader_name)
    bot_move = trainer_bot.decide_action(strategy=bot_strategy)
    # 교체가 발생했을 수 있으므로 갱신된 봇 상태도 반영
    st.session_state.pending_bot_move = bot_move

def process_turn(player_move):
    """
    [한 턴의 배틀 진행 처리]
    봇의 행동은 이미 prepare_bot_move()를 통해 세션에 저장되어 있으며,
    이 함수는 저장된 봇 행동을 가져와 배틀 로직을 실행합니다.
    """
    # 1. 플레이어 교체 처리 (턴 소모)
    if player_move.get("category") == "switch":
        target_idx = player_move["target_index"]
        st.session_state.battle_player = st.session_state.player_party[target_idx]
        
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    bot_party = st.session_state.bot_party
    
    # =========================== 봇의 행동 결정 로직 =============================
    # 미리 계산된 봇 행동을 가져옴. 없으면 즉시 계산 (안전망)
    bot_move = st.session_state.pop("pending_bot_move", None)
    if bot_move is None:
        bot_strategy = st.session_state.get("bot_strategy", "llm")
        trainer_bot = BattleBot(leader_name=st.session_state.leader_name)
        bot_move = trainer_bot.decide_action(strategy=bot_strategy)

    # 봇 교체 행동이라면 플레이어 입력 이후인 지금 시점에 battle_bot 갱신
    # (prepare_bot_move에서는 결정만 하고 세션 상태를 변경하지 않음)
    if bot_move and bot_move.get("category") == "switch" and bot_move.get("is_bot"):
        target_idx = bot_move["target_index"]
        st.session_state.battle_bot = st.session_state.bot_party[target_idx]

    bot = st.session_state.battle_bot  # 갱신된 봇 참조
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
        # 체육관 이름을 선택지에 노출
        gym_options = list(GYM_NAME_MAP.values())
        # 역매핑 (체육관 이름 -> 관장 이름)
        GYM_TO_LEADER = {v: k for k, v in GYM_NAME_MAP.items()}
        
        # 현재 세션의 선택된 관장에 해당하는 체육관 이름 찾기
        current_leader = st.session_state.get("selected_leader", "웅이")
        current_gym = GYM_NAME_MAP.get(current_leader, gym_options[0])
        default_idx = gym_options.index(current_gym) if current_gym in gym_options else 0

        selected_gym = st.selectbox("대결할 체육관을 선택하세요", options=gym_options, index=default_idx)
        selected_leader = GYM_TO_LEADER[selected_gym]
        st.session_state.selected_leader = selected_leader
        
        leader_roster = ROSTER_MAP.get(selected_leader, [])
        if leader_roster:
            st.caption(f"**{selected_leader}({selected_gym})의 엔트리:**")
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
                    st.rerun()
                
                if st.button("⬅️ 메뉴로 돌아가기", use_container_width=True):
                    st.session_state.battle_stage = "menu"
                    st.rerun()
    
    elif st.session_state.battle_stage == "battle":
        # 배틀 진행 화면 (battle.py 로직과 유사)
        player = st.session_state.battle_player
        bot = st.session_state.battle_bot
        
        # ─── 0. Dynamic Background ───
        leader_name = st.session_state.get("leader_name", "관장")
        gym_bg = get_gym_bg_base64(leader_name)
        inject_battle_styles(bg_url=gym_bg)

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
            st.markdown("<div style='color: #94a3b8; font-weight: 800; margin-bottom: 8px;'>   BATTLE LOG</div>", unsafe_allow_html=True)
            history_container = st.container(height=450)
            with history_container:
                for message in st.session_state.battle_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"], unsafe_allow_html=True)
        
        with i_col2:
            st.markdown("<div style='color: #94a3b8; font-weight: 800; margin-bottom: 8px;'>TRAINER COMMAND</div>", unsafe_allow_html=True)
            input_container = st.container()
            with input_container:
                        
                # 대기 중인 메시지가 있다면 지연을 두고 하나씩 출력
                if "pending_messages" in st.session_state and st.session_state.pending_messages:
                    for msg_event in st.session_state.pending_messages:
                        time.sleep(0.8) # 0.8초 딜레이
                        
                        # 1. 상태 업데이트 및 동기화
                        msg_text = msg_event["message"]
                        p_state = msg_event["player_state"]
                        b_state = msg_event["bot_state"]
                        
                        is_bot_switch = msg_event.get("bot_switch")
                        
                        if not is_bot_switch:
                            # ── 일반 이벤트: 상태 갱신 → UI 갱신 → 메시지 출력 ──
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
                                render_pokemon_status("MY POKEMON", player)
                            with bot_placeholder:
                                render_pokemon_status(f"BOT ({leader_name})", bot, reveal_details=False)
                            
                        # 3. 메시지 출력
                            with history_container:
                                with st.chat_message("assistant"):
                                    st.markdown(msg_text, unsafe_allow_html=True)
                            st.session_state.battle_messages.append({"role": "assistant", "content": msg_text})
                        
                        else:
                            # ── 봇 교체 이벤트: 메시지 먼저 출력 → 봇 교체 → UI 갱신 ──
                            # 1) 교체 전 상태로 플레이어 HP바만 먼저 갱신
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
                            
                            # 2) 교체 메시지 출력
                            with history_container:
                                with st.chat_message("assistant"):
                                    st.markdown(msg_text, unsafe_allow_html=True)
                            st.session_state.battle_messages.append({"role": "assistant", "content": msg_text})
                            
                            # 3) 딜레이 후 봇 교체 + 이미지·HP바 갱신
                            time.sleep(0.6)
                            next_idx = msg_event["bot_next_index"]
                            st.session_state.battle_bot = st.session_state.bot_party[next_idx]
                            bot = st.session_state.battle_bot
                            with bot_placeholder:
                                render_pokemon_status(f"BOT ({leader_name})", bot, reveal_details=False)
                        
                    st.session_state.pending_messages = []
                    
                    # 애니메이션 종료 후 상태 판별 (현재 player, bot은 최종 상태임)
                    battle_continues = True
                    if bot.current_hp <= 0:
                        alive_bots = [bp for bp in st.session_state.bot_party if bp.current_hp > 0]
                        if not alive_bots:
                            st.session_state.battle_over = True
                            st.session_state.winner = "사용자"
                            battle_continues = False
                            
                    if player.current_hp <= 0:
                        alive_players = [pp for pp in st.session_state.player_party if pp.current_hp > 0]
                        if alive_players:
                            st.session_state.waiting_for_switch = True
                        else:
                            st.session_state.battle_over = True
                            st.session_state.winner = st.session_state.get("leader_name", "관장")
                            battle_continues = False
                    
                    # ─── 다음 턴 봇 행동 사전 결정 ───
                    # 배틀이 아직 진행 중이고 플레이어 교체 대기 중이 아닐 때만 미리 계산
                    if battle_continues and not st.session_state.get("waiting_for_switch", False):
                        prepare_bot_move()
                            
                    st.rerun()

                if st.session_state.get("battle_over", False):
                    winner = st.session_state.winner
                    if winner == "사용자":
                        quotes = LEADER_QUOTES.get(st.session_state.leader_name, {"defeat": "훌륭한 승리였습니다!"})
                        st.markdown(f"""
                            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                                <div style="color: #10b981; font-weight: 900; font-size: 1.2rem; margin-bottom: 10px;">🏆 배틀 승리!</div>
                                <div style="color: #e2e8f0; font-style: italic; font-size: 1rem;">{st.session_state.leader_name}: "{quotes['defeat']}"</div>
                                <div style="color: #e2e8f0; font-size: 0.9rem; margin-top: 10px;">{st.session_state.leader_name}과(와)의 승부에서 이겼다!</div>
                            </div>
                        """, unsafe_allow_html=True)
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
                                # 교체 실행 — 메시지를 pending_messages에 담아 화면 출력 흐름에 합류
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
                                # 교체 후 다음 턴 봇 행동 미리 계산
                                prepare_bot_move()
                                st.rerun()
                else:
                    st.write("---")
                    st.subheader("무엇을 할까?")
                    
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

                    st.write("---")
                    if st.button("🚫 배틀 중단", use_container_width=True):
                        st.session_state.battle_started = False
                        st.session_state.battle_stage = "menu"
                        st.rerun()

if __name__ == "__main__":
    show()
