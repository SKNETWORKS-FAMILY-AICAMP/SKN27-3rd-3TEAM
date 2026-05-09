sequenceDiagram
    actor Player
    participant BattleSystem
    participant Database
    participant LLM_Bot

    %% Phase 0: Pre-Battle Setup (신규 추가)
    Note over Player, LLM_Bot: Phase 0: 배틀 준비 및 엔트리 설정
    Player->>BattleSystem: 최종 진화체 포켓몬 1마리 및 기술 4개 선택
    BattleSystem->>Database: 플레이어 포켓몬 스탯 및 기술 위력/명중률 조회
    Database-->>BattleSystem: 플레이어 데이터 적재
    BattleSystem->>LLM_Bot: 실전 포켓몬 및 기술 세팅 프롬프트 주입 (페르소나 부여)
    BattleSystem->>Database: LLM 포켓몬 스탯 및 기술 정보 조회
    Database-->>BattleSystem: LLM 데이터 적재

    %% Phase 1: Initialization
    Note over Player, LLM_Bot: Phase 1: 배틀 시작
    BattleSystem->>Player: 배틀 시작 알림 (UI 렌더링)
    
    loop 배틀 진행 (양쪽 중 하나가 기절할 때까지)
        %% Phase 2: Action Selection (LLM 통신 추가)
        Note over Player, LLM_Bot: Phase 2: 커맨드 입력
        Player->>BattleSystem: 기술(Move) 선택
        
        BattleSystem->>LLM_Bot: 현재 턴의 배틀 상태 전달 (양측 남은 체력, 타입 상성 등)
        LLM_Bot-->>BattleSystem: 상황 판단 후 실전 기술(Move) 선택 및 반환
        
        %% Phase 3: Speed Check & Action Order
        Note over BattleSystem: Phase 3: 턴 순서 판정
        BattleSystem->>BattleSystem: 양측 스피드 스탯 비교 및 선공/후공 결정
        
        %% Phase 4: First Attack Resolution
        Note over BattleSystem: Phase 4-A: 선공 포켓몬의 공격
        BattleSystem->>Database: 기술 상성 배율(type_efficacy) 조회
        Database-->>BattleSystem: 상성 결과 반환
        BattleSystem->>BattleSystem: 데미지 계산 및 후공 포켓몬 HP 차감
        BattleSystem->>Player: 선공 결과 메세지 출력 (UI 업데이트)
        
        %% Phase 5: Faint Check 1
        alt 후공 포켓몬 HP <= 0
            BattleSystem->>BattleSystem: 후공 포켓몬 기절 판정
        else 후공 포켓몬 생존
            %% Phase 6: Second Attack Resolution
            Note over BattleSystem: Phase 4-B: 후공 포켓몬의 공격
            BattleSystem->>Database: 기술 상성 배율(type_efficacy) 조회
            Database-->>BattleSystem: 상성 결과 반환
            BattleSystem->>BattleSystem: 데미지 계산 및 선공 포켓몬 HP 차감
            BattleSystem->>Player: 후공 결과 메세지 출력 (UI 업데이트)
            
            %% Phase 7: Faint Check 2
            opt 선공 포켓몬 HP <= 0
                BattleSystem->>BattleSystem: 선공 포켓몬 기절 판정
            end
        end
    end
    
    %% Phase 8: Battle End
    Note over Player, LLM_Bot: Phase 5: 배틀 종료
    BattleSystem->>Player: 승패 결과 출력