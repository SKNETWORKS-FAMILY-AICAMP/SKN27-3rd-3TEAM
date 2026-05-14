import streamlit as st
import random
from battle.trainerbot import ROSTER_MAP
from battle.utils import BotBattlePokemon

class BattleBot:
    @classmethod
    def initialize(cls, leader_name: str):
        """
        배틀 시작 시 최초 1회 호출되어 봇의 파티를 구성합니다.
        """
        leader_roster = ROSTER_MAP.get(leader_name, [])
        # 관장의 전체 엔트리 중 랜덤 3마리 선택
        bot_entries = random.sample(leader_roster, min(3, len(leader_roster)))
        
        # 봇의 엔트리 정보 초기화
        battle_pokemons = []
        for pokemon in bot_entries:
            # 관장 포켓몬 보정 로직
            if leader_name == "지우" and pokemon['name'] == "피카츄":
                # 지우의 피카츄: 모든 능력치 2배 (전기구슬 효과)
                multiplier = 2.0
            else:
                # 그 외 모든 관장의 포켓몬: 모든 능력치 1.1배 보정 (난이도 향상)
                multiplier = 1.1

            battle_pokemons.append(BotBattlePokemon(
                id=pokemon['id'], 
                name=pokemon['name'], 
                selected_moves=pokemon['moves'],
                multiplier=multiplier
            ))

        # session_state 초기화
        st.session_state.bot_party = battle_pokemons
        st.session_state.battle_bot = battle_pokemons[0]
        return battle_pokemons

    def __init__(self, leader_name: str, battle_state=st.session_state):
        """
        leader_name: 관장의 이름 (예: "웅이", "이슬이")
        battle_state: 현재 배틀의 상황
            - battle_player: 플레이어가 출전 시킨 포켓몬
            - battle_bot: 봇이 출전 시킨 포켓몬
            - bot_party: 봇의 포켓몬 엔트리
        """
        # 관장 정보 및 전체 로스터 정보
        self.leader_name = leader_name
        self.full_roster = ROSTER_MAP.get(self.leader_name, [])

        # session_state에 저장된 현재 배틀 상태
        self.battle_state = battle_state

        # 현재 봇이 출전시킨 포켓몬 정보, 엔트리 정보, 출전한 포켓몬 이외의 대기 중인 포켓몬 정보
        self.battle_bot = battle_state.battle_bot
        self.bot_party = battle_state.bot_party
        self.bot_alive_other_pokemons = [bp for bp in self.bot_party if bp.id != self.battle_bot.id and bp.current_hp > 0]

        # 현재 플레이어가 출전시킨 포켓몬 정보, 엔트리 정보, 출전한 포켓몬 이외의 대기 중인 포켓몬 정보
        self.battle_player = battle_state.battle_player
        self.player_party = battle_state.player_party
        self.player_alive_other_pokemons = [pp for pp in self.player_party if pp.id != self.battle_player.id and pp.current_hp > 0]

    def decide_action(self, strategy="llm"):
        """
        현재 배틀 상태를 기반으로 봇이 취할 행동을 결정합니다.
        """
        if strategy == "random":
            return self._decide_random()
        elif strategy == "llm":
            return self._decide_llm()
        elif strategy == "rag":
            return self._decide_rag()
        else:
            return self._decide_random()

    def _decide_random(self):
        """
        무작위로 행동을 결정합니다.
        (15% 확률로 교체, 그 외에는 무작위 기술 사용)
        """
        # 포켓몬 교체 결정: 생존한 다른 포켓몬이 있다면 15% 확률로 교체
        if self.bot_alive_other_pokemons and random.random() < 0.15:
            target_bot = random.choice(self.bot_alive_other_pokemons)
            target_idx = self.bot_party.index(target_bot)
            bot_move = {
                "name": f"{target_bot.name}(으)로 교체",
                "category": "switch",
                "target_index": target_idx,
                "priority": 6,
                "is_bot": True
            }
            # 실제 세션 상태 갱신은 process_turn()에서 수행됩니다.
            return bot_move
        else:
            # 기술 사용 결정
            return random.choice(self.battle_bot.moves)

    def _decide_llm(self):
        """
        LLM 기반으로 최적의 행동을 결정합니다.
        (LangGraph 워크플로우를 통해 분석 후 결정)
        """
        from battle.llm import get_llm_battle_decision
        from dataclasses import asdict
        
        try:
            # 1. 현재 배틀 상태를 딕셔너리로 변환
            bot_dict = asdict(self.battle_bot)
            player_dict = asdict(self.battle_player)
            party_dicts = [asdict(p) for p in self.bot_party]
            
            # 2. LLM 의사결정 엔진 호출
            decision = get_llm_battle_decision(bot_dict, player_dict, party_dicts)
            
            # 3. 결정 내용 처리
            if decision.get('action_type') == 'switch':
                # 교체 가능한 아군 포켓몬 리스트 재계산 (llm 노드와 동일한 기준)
                alive_others = [p for p in self.bot_party if p.id != self.battle_bot.id and p.current_hp > 0]
                
                idx = decision.get('action_index', 0)
                if idx < len(alive_others):
                    target_bot = alive_others[idx]
                    target_idx = self.bot_party.index(target_bot)
                    
                    bot_move = {
                        "name": f"{target_bot.name}(으)로 교체",
                        "category": "switch",
                        "target_index": target_idx,
                        "priority": 6,
                        "is_bot": True
                    }
                    # 실제 세션 상태 갱신은 process_turn()에서 수행됩니다.
                    return bot_move
            
            # 기술 사용 결정 (또는 교체 실패 시 기본값)
            move_name = decision.get('action_name')
            selected_move = next((m for m in self.battle_bot.moves if m['name'] == move_name), None)
            
            # 만약 매칭되는 기술이 없으면 무작위 선택 (안전 장치)
            return selected_move if selected_move else random.choice(self.battle_bot.moves)
            
        except Exception as e:
            # 에러 발생 시 랜덤 전략으로 폴백
            print(f"LLM Decision Error: {e}")
            return self._decide_random()

    def _decide_rag(self):
        """
        RAG(지식 베이스) 기반으로 최적의 행동을 결정합니다.
        (현재는 LLM 전략과 동일하게 동작하며 추후 RAG 로직 추가 예정)
        """
        return self._decide_llm()