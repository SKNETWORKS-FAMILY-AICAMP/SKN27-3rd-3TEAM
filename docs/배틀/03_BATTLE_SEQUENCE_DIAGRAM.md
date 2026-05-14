# 배틀 시스템 시퀀스 다이어그램

## 개요

배틀 시스템의 주요 흐름을 시퀀스 다이어그램으로 표현합니다. 

---

## 1. 전체 배틀 흐름 (High-Level)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        배틀 시작 (Battle Init)                       │
├─────────────────────────────────────────────────────────────────────┤

[Frontend]          [Backend API]           [Database]
    │                   │                        │
    │  POST /start      │                        │
    ├──────────────────>│                        │
    │                   │                        │
    │                   │ SELECT * FROM pokemon  │
    │                   ├───────────────────────>│
    │                   │                        │
    │                   │ pokemon_dict (3개 선택) │
    │                   │<───────────────────────┤
    │                   │                        │
    │                   │ → load_bot_pokemon()   │
    │                   │   (스탯, 기술 로드)      │
    │                   │                        │
    │                   │ → decide_action()      │
    │                   │   (첫 턴 기술 선택)     │
    │                   │                        │
    │   {bot_party,     │                        │
    │    first_move}    │                        │
    │<──────────────────┤                        │
    │                   │                        │
    │ [화면에 렌더링]    │                        │
    │ - 봇 포켓몬 3마리  │                        │
    │ - 플레이어 팀      │                        │
    │                   │                        │
    └─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                   1턴 배틀 처리 (Turn Processing)                    │
├─────────────────────────────────────────────────────────────────────┤

[Player]          [Frontend]              [Backend API]     [Database]
  │                 │                        │                  │
  │ [기술 선택]     │                        │                  │
  │─────────────────>│                        │                  │
  │                 │ POST /process_turn     │                  │
  │                 │ {user_poke, bot_poke, │                  │
  │                 │  user_move, bot_move}  │                  │
  │                 ├───────────────────────>│                  │
  │                 │                        │                  │
  │                 │                        │ run_battle_logic()│
  │                 │                        │ ├─ 우선도 결정   │
  │                 │                        │ ├─ 선공 기술 처리 │
  │                 │                        │ ├─ 후공 기술 처리 │
  │                 │                        │ ├─ 상태이상 처리  │
  │                 │                        │ └─ 턴 종료 효과   │
  │                 │                        │   (독, 화상)      │
  │                 │                        │                  │
  │                 │   {messages,           │                  │
  │                 │    final_states,       │                  │
  │                 │    battle_over,        │                  │
  │                 │    winner}             │                  │
  │                 │<───────────────────────┤                  │
  │                 │                        │                  │
  │ [메시지 표시]   │                        │                  │
  │ - 공격 로그     │                        │                  │
  │ - 데미지        │                        │                  │
  │ - 상태 갱신     │                        │                  │
  │                 │                        │                  │
  │ [배틀 종료?]    │                        │                  │
  │ ├─ 아니오 → 다음 턴 준비                  │                  │
  │ └─ 예    → 결과 화면                      │                  │
  │                 │                        │                  │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 포켓몬 로드 (pokemon_loader 모듈)

```
┌─────────────────────────────────────────────────────┐
│   load_bot_pokemon(pokemon_id, moves, level)        │
├─────────────────────────────────────────────────────┤

Neo4j 또는 RDB 조회
│
├─ [1] 포켓몬 기본 정보
│  ├─ id, name, types
│  ├─ image_url, cry_url
│  └─ level (기본값: 50)
│
├─ [2] 스탯 조회
│  └─ hp, attack, defense, sp_attack, sp_defense, speed
│     × level_multiplier (봇: 1.1 또는 2.0)
│
├─ [3] 기술(Moves) 조회
│  ├─ Neo4j: pokemon → CAN_LEARN → move
│  ├─ RDB:   pokemon_moves + moves 테이블
│  └─ 필터링: selected_moves만 로드 (메모리 최적화)
│
├─ [4] 타입 조회
│  ├─ pokemon_types 테이블에서 type_id 추출
│  └─ 최대 2개의 타입
│
└─ [Return] 포켓몬 객체 (dict)
   {
       "id": 25,
       "name": "피카츄",
       "level": 50,
       "current_hp": 95,
       "stats": {hp: 95, attack: 55, ...},
       "types": [13, 14],
       "moves": [
           {id: 4, name: "전광석화", type_id: 13, power: 90, ...},
           ...
       ],
       "stat_changes": {attack: 0, defense: 0, ...},
       "ailment": null
   }
```

---

## 3. 턴 처리 상세 흐름 (run_battle_logic)

```
┌──────────────────────────────────────────────────────────┐
│   run_battle_logic(user_poke, bot_poke,                 │
│                     user_move, bot_move)                  │
├──────────────────────────────────────────────────────────┤

[Input Validation]
│ ├─ 모든 포켓몬 alive 확인 (HP > 0)
│ ├─ 기술 존재 확인
│ └─ 기술 사용 가능한가 (교체일 경우 예외)
│
├─────────────────────────────────────────
│ [Step 1] 우선도(Priority) 결정
├─────────────────────────────────────────
│
│ user_priority  = user_move.priority
│ bot_priority   = bot_move.priority
│
│ IF user_priority > bot_priority:
│     first_attacker = user
│     second_attacker = bot
│ ELIF bot_priority > user_priority:
│     first_attacker = bot
│     second_attacker = user
│ ELSE:
│     // 우선도가 같으면 스피드 비교
│     IF user_speed > bot_speed:
│         first_attacker = user
│     ELSE:
│         first_attacker = bot
│
│ [Log] "피카츄가 먼저 나간다!"
│
├─────────────────────────────────────────
│ [Step 2] 선공(First) 기술 처리
├─────────────────────────────────────────
│
│ processor = MoveProcessor(
│     attacker = first_attacker,
│     defender = second_attacker,
│     move = first_move
│ )
│ messages += processor.execute()
│
│ 처리 내용:
│ ├─ 교체 확인 (기술 = "switch")
│ ├─ 상태이상 확인 (마비 → 25% 행동 불가)
│ ├─ 명중 판정 (accuracy vs evasion)
│ ├─ 데미지 계산
│ │  ├─ base_damage = (2*level/5+2) * power * (A/D) / 50 + 2
│ │  ├─ STAB 보정 (같은 타입 +25%)
│ │  ├─ 타입 상성 보정 (× 2.0, 1.0, 0.5, 0.0)
│ │  ├─ 급소 (5-10% 확률 × 1.5)
│ │  └─ 화상 (physical 기술 × 0.5)
│ ├─ 스탯 변화 적용
│ ├─ 상태이상 부여
│ └─ 회복 처리
│
│ // 선공이 제거했는지 확인?
│ IF first_attacker_hp <= 0:
│     [Log] "피카츄는 쓰러졌다!"
│     messages.append(faint_message)
│     // 후공은 행동할 수 없음
│     RETURN messages
│
├─────────────────────────────────────────
│ [Step 3] 후공(Second) 기술 처리
├─────────────────────────────────────────
│
│ // 후공 포켓몬이 아직 살아있는지 확인
│ IF second_attacker_hp > 0:
│     processor = MoveProcessor(...)
│     messages += processor.execute()
│
│     IF second_attacker_hp <= 0:
│         [Log] "리자몽은 쓰러졌다!"
│
├─────────────────────────────────────────
│ [Step 4] 턴 종료 효과 (Residual Damage)
├─────────────────────────────────────────
│
│ FOR each pokemon in [user_poke, bot_poke]:
│     IF pokemon.ailment == "burn":
│         damage = pokemon.stats.hp // 8
│         pokemon.current_hp -= damage
│         [Log] "불꽃은 ~을(를) 괴롭히고 있다! (N 데미지)"
│
│     ELIF pokemon.ailment == "poison":
│         damage = pokemon.stats.hp // 8
│         pokemon.current_hp -= damage
│         [Log] "~은(는) 독 피해를 입었다!"
│
├─────────────────────────────────────────
│ [Step 5] 결과 생성
├─────────────────────────────────────────
│
│ RETURN {
│     "messages": messages,
│     "user_pokemon": {updated user state},
│     "bot_pokemon": {updated bot state},
│     "user_party": [...],
│     "bot_party": [...]
│ }
│
└──────────────────────────────────────────────────────────┘
```

---

## 4. 기술 처리 상세 흐름 (MoveProcessor.execute)

```
┌────────────────────────────────────────────────────────┐
│    MoveProcessor(attacker, defender, move).execute()   │
├────────────────────────────────────────────────────────┤

[Input] 공격자, 방어자, 기술

├─ [1] 교체 여부 확인
│  IF move.name == "switch" OR move.category == "switch":
│      [Log] "가서, {defender_name}!"
│      RETURN [switch_message]
│
├─ [2] 상태이상 확인 (Only 공격자)
│  IF attacker.ailment == "paralysis":
│      IF random() < 0.25:
│          [Log] "~은(는) 마비 상태여서 움직일 수 없다!"
│          RETURN [paralysis_message]
│
│  IF attacker.ailment == "sleep":
│      IF sleep_turns > 0:
│          [Log] "~은(는) 깊은 잠에 빠져있다!"
│          sleep_turns--
│          RETURN [sleep_message]
│
├─ [3] 명중 판정
│  accuracy_rate = move.accuracy * (attacker.accuracy_stage)
│  evasion_rate = defender.evasion_stage
│
│  hit_probability = (accuracy_rate / 100) / evasion_rate
│
│  IF random() > hit_probability:
│      [Log] "~의 공격이 빗나갔다!"
│      RETURN [miss_message]
│
├─ [4] 기술 유형별 처리
│  │
│  ├─ damage: calculate_damage()
│  ├─ status: apply_status_ailment()
│  ├─ heal: apply_healing()
│  └─ damage-fixed: apply_fixed_damage()
│
├─ [5] 데미지 적용 (if damage move)
│  base_damage = calculate_damage()
│  IF base_damage > 0:
│      actual_damage = apply_critical_hit(base_damage)
│      defender.current_hp -= actual_damage
│      [Log] "N의 데미지!"
│
├─ [6] 부가 효과 처리 (Secondary effects)
│  IF move.ailment:
│      IF random() < move.ailment_chance:
│          [Log] "~는 마비되었다!"
│          defender.ailment = move.ailment
│
│  IF move.stat_changes:
│      FOR each stat_name, stat_change in move.stat_changes:
│          IF random() < move.stat_chance:
│              defender.stat_changes[stat_name] += stat_change
│              [Log] "~의 {stat_name}이(가) {↑↓}했다!"
│
│  IF move.drain > 0:
│      heal_amount = actual_damage * (move.drain / 100)
│      attacker.current_hp += heal_amount
│      [Log] "~은(는) 상대의 체력을 흡수했다!"
│
│  IF move.flinch_chance > 0:
│      IF random() < move.flinch_chance:
│          defender.flinch = True  // 다음 턴 행동 불가
│
├─ [7] 메시지 생성
│  RETURN [
│      {message: "...", player_state: {...}, bot_state: {...}},
│      {message: "...", player_state: {...}, bot_state: {...}},
│      ...
│  ]
│
└────────────────────────────────────────────────────────┘
```

---

## 5. 데미지 계산 흐름 (calculate_damage)

```
┌─────────────────────────────────────────────────────┐
│     calculate_damage(attacker, defender, move)      │
├─────────────────────────────────────────────────────┤

[1] 고정 데미지 기술인가?
    IF move.category == "damage-fixed":
        power = get_fixed_damage(move)
        RETURN power
    
    // 예: 목숨걸기 → 레벨만큼 데미지

[2] 관여 스탯 결정
    IF move.damage_class == "physical":
        base_atk = attacker.stats.attack
        base_def = defender.stats.defense
        atk_stage = attacker.stat_changes.attack
        def_stage = defender.stat_changes.defense
    ELSE if move.damage_class == "special":
        base_atk = attacker.stats.sp_attack
        base_def = defender.stats.sp_defense
        atk_stage = attacker.stat_changes.sp_attack
        def_stage = defender.stat_changes.sp_defense

[3] 스탯 스테이지 적용
    // 스탯 스테이지는 -6 ~ +6 범위
    // 공격 쪽이 양수면 유리, 방어 쪽이 양수면 유리
    
    if atk_stage >= 0:
        atk = base_atk * (2 + atk_stage) / 2
    else:
        atk = base_atk * 2 / (2 - atk_stage)
    
    if def_stage >= 0:
        def = base_def * (2 + def_stage) / 2
    else:
        def = base_def * 2 / (2 - def_stage)

[4] 기본 데미지 계산
    base_damage = (2 × level / 5 + 2) × power × (A / D) / 50 + 2
    
    // 예: level=50, power=90, A=100, D=100
    // base_damage = (100/5 + 2) × 90 × (100/100) / 50 + 2
    //             = 22 × 90 / 50 + 2
    //             = 39.6 + 2 ≈ 41

[5] 자속 보정 (STAB)
    IF attack_type_id IN attacker.types:
        stab_multiplier = 1.5
    ELSE:
        stab_multiplier = 1.0

[6] 타입 상성 보정
    type_multiplier = type_efficacy[attack_type_id][defender_type_ids]
    
    // 예: 전기 기술이 물 포켓몬에 → 2.0
    // 전기 기술이 풀 포켓몬에 → 0.5

[7] 상태이상 보정 (화상)
    IF move.damage_class == "physical" AND attacker.ailment == "burn":
        burn_multiplier = 0.5
    ELSE:
        burn_multiplier = 1.0

[8] 최종 데미지
    final_damage = int(base_damage × stab × type_multiplier × burn_multiplier)
    
    RETURN final_damage

// 예시 계산:
// 피카츄 (Lv.50) 전광석화 vs 리자몽
// base_damage = 41
// STAB = 1.5 (전기)
// 타입 상성 = 2.0 (물은 전기에 약함? 아니, 리자몽은 불)
// → 실제로 불 포켓몬은 전기에 1배
// final_damage = 41 × 1.5 × 1.0 × 1.0 = 61
```

---

## 6. 봇 행동 결정 (decide_action)

```
┌─────────────────────────────────────────────────────┐
│   decide_action(bot_pokemon, player_pokemon,        │
│                 bot_party, strategy="llm")          │
├─────────────────────────────────────────────────────┤

[1] 행동 선택 풀 생성
    possible_actions = []
    
    # 현재 포켓몬의 모든 기술
    FOR each move in bot_pokemon.moves:
        possible_actions.append({
            "type": "move",
            "action": move
        })
    
    # 교체 가능한 포켓몬들 (현재 포켓몬 제외, HP > 0)
    FOR each pokemon in bot_party:
        IF pokemon.id != bot_pokemon.id AND pokemon.current_hp > 0:
            possible_actions.append({
                "type": "switch",
                "action": pokemon
            })

[2] 전략 선택
    IF strategy == "random":
        RETURN random.choice(possible_actions)
    
    ELIF strategy == "llm":
        RETURN llm_decision(bot_pokemon, player_pokemon, 
                           bot_party, possible_actions)

[3] LLM 기반 결정 (LangChain)
    │
    ├─ [Prompt 구성]
    │  "현재 상황:"
    │  "- 봇 포켓몬: {bot_pokemon.name} (HP: {bot_pokemon.current_hp}/{bot_pokemon.stats.hp})"
    │  "- 상대 포켓몬: {player_pokemon.name} (HP: {player_pokemon.current_hp}/{player_pokemon.stats.hp})"
    │  "- 타입 상성: {유리/불리}"
    │  "- 가능한 행동:"
    │  "  1. {move1.name} (위력: {move1.power}, 명중: {move1.accuracy})"
    │  "  2. {move2.name} ..."
    │  "  3. {pokemon1.name}으로 교체"
    │  "위의 상황에서 가장 나은 행동을 선택하고 이유를 설명하세요."
    │
    ├─ [LLM 호출] (Groq LLM)
    │  response = llm.generate(prompt)
    │  // 예: "전광석화를 사용하세요. 상대의 약점이기 때문입니다."
    │
    ├─ [응답 파싱]
    │  IF response contains "전광석화":
    │      action = bot_pokemon.moves.find(name="전광석화")
    │  ELIF response contains "교체":
    │      action = best_switch_candidate()
    │
    └─ RETURN action

[4] 반환값
    {
        "type": "move" or "switch",
        "target": {move or pokemon dict}
    }

└─────────────────────────────────────────────────────┘
```

---

## 7. 배틀 종료 판정 (process_turn 반환 후)

```
┌───────────────────────────────────────────────┐
│         배틀 종료 판정 (Battle Over Check)     │
├───────────────────────────────────────────────┤

[1] 봇 포켓몬 사망 확인
    current_bot_id = bot_pokemon.id
    alive_bots = [p for p in bot_party if p.current_hp > 0 and p.id != current_bot_id]
    
    IF bot_pokemon.current_hp <= 0 AND len(alive_bots) == 0:
        battle_over = True
        winner = "Player"
        [Log] "플레이어가 승리했다!"

[2] 플레이어 포켓몬 사망 확인
    current_player_id = user_pokemon.id
    alive_players = [p for p in player_party if p.current_hp > 0 and p.id != current_player_id]
    
    IF user_pokemon.current_hp <= 0 AND len(alive_players) == 0:
        battle_over = True
        winner = "Bot"
        [Log] "봇이 승리했다!"

[3] 배틀 진행 중
    ELSE:
        battle_over = False
        winner = None
        
        // 봇 포켓몬이 사망했으면 교체
        IF bot_pokemon.current_hp <= 0:
            next_bot = alive_bots[0]
            [Log] "관장은 {next_bot.name}을(를) 내보냈다!"
            prepare for next turn with next_bot

└───────────────────────────────────────────────┘
```

---

## 8. 배틀 상태 다이어그램

```
          ┌─────────────────┐
          │  배틀 준비 (INIT)  │
          └────────┬────────┘
                   │
                   ▼
    ┌─────────────────────────────┐
    │  턴 대기 (WAITING_FOR_INPUT)   │
    │ - 플레이어 기술 선택          │
    │ - 봇 행동 사전 계산           │
    └────────┬────────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │   턴 처리 (PROCESSING_TURN) │
    │ - 우선도 결정             │
    │ - 선공/후공 기술 실행      │
    │ - 턴 종료 효과            │
    └────────┬─────────────────┘
             │
             ├─────────────────────────┐
             │                         │
             ▼                         ▼
    ┌─────────────────┐      ┌──────────────┐
    │  배틀 진행 (ONGOING) │      │ 배틀 종료 (OVER) │
    │                 │      │              │
    │ - HP 업데이트   │      │ - 승자 결정  │
    │ - 상태이상 적용 │      │ - 결과 저장  │
    └────────┬────────┘      └──────────────┘
             │
             └─► [턴 대기로 돌아감 (if not over)]
                 또는
                 [배틀 종료 (if over)]
```

---

## 9. 에러 처리 흐름

```
┌────────────────────────────────────────┐
│        예외 상황 처리                   │
├────────────────────────────────────────┤

TRY:
    messages = run_battle_logic(...)
    
    // Possible Errors:
    // 1. 포켓몬 데이터 누락
    // 2. 기술 데이터 누락
    // 3. 타입 데이터 누락
    // 4. 부동소수점 계산 오버플로우
    // 5. 상태 불일치 (HP > max_hp 등)

EXCEPT Exception as e:
    [Log] Error with traceback
    
    RETURN {
        "status_code": 500,
        "detail": str(e),
        "error_type": type(e).__name__
    }
    
    // Frontend: 에러 메시지 표시
    // 사용자: 처음부터 재시작
```

---

## 10. 예시: 1턴 처리 결과

```
POST /api/v1/battle/process_turn

Request:
{
    "user_pokemon": {...피카츄...},
    "bot_pokemon": {...리자몽...},
    "user_move": {name: "전광석화", ...},
    "bot_move": {name: "화염방사", ...},
    "leader_name": "웅이"
}

Response:
{
    "messages": [
        {
            "message": "피카츄가 먼저 나간다!",
            "player_state": {...},
            "bot_state": {...}
        },
        {
            "message": "피카츄의 전광석화!",
            "player_state": {...},
            "bot_state": {...}
        },
        {
            "message": "리자몽에게 67의 데미지!",
            "player_state": {...},
            "bot_state": {current_hp: 33, ...}
        },
        {
            "message": "리자몽의 화염방사!",
            "player_state": {...},
            "bot_state": {...}
        },
        {
            "message": "피카츄에게 45의 데미지!",
            "player_state": {current_hp: 50, ...},
            "bot_state": {...}
        }
    ],
    "battle_over": false,
    "winner": null,
    "final_user_pokemon": {...피카츄..., current_hp: 50},
    "final_bot_pokemon": {...리자몽..., current_hp: 33}
}
```

