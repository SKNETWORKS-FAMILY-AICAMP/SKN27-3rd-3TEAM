from typing import TypedDict, Optional

class PokemonChatState(TypedDict):
    # 입력
    question    : str

    # 라우터 결과
    intent      : str        # "sql" | "vector" | "graph"

    # 각 검색 결과
    sql_result  : list       # PostgreSQL 결과
    vector_result: list      # Elasticsearch 결과
    graph_result : list      # Neo4j 결과

    # 최종
    context     : list       # 통합 컨텍스트
    answer      : str        # 최종 답변
    retry_count : int        # 재시도 횟수