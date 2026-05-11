"""
Vector search node for Team Build Hybrid RAG.

목적:
    Graph DB가 계산한 팀 분석/추천 결과에, pgvector에 저장된 텍스트 근거를 추가로 붙입니다.
    예를 들면 포켓몬 설명, 도감 문장, 특성 효과, 기술 효과 같은 문서를 검색해서
    최종 답변이 단순 점수 나열이 아니라 "왜 그런지" 설명할 수 있게 만듭니다.
"""

import os
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import engine
from team_build_rag.state import HybridRagState

try:
    # OpenAI 임베딩은 기존 database/postgre/utils/vectorizer.py와 같은 모델을 사용합니다.
    from openai import OpenAI
except ImportError:  # pragma: no cover - 배포 환경에서 패키지가 빠진 경우를 안전하게 처리합니다.
    OpenAI = None


# EMBEDDING_MODEL:
# - vectorizer.py에서 사용한 모델과 맞춰야 DB에 저장된 embedding 차원과 검색 embedding 차원이 일치합니다.
EMBEDDING_MODEL = "text-embedding-3-small"

# DEFAULT_VECTOR_LIMIT:
# - 테이블별로 너무 많은 문서를 가져오면 답변 근거가 흐려지므로 상위 몇 개만 사용합니다.
DEFAULT_VECTOR_LIMIT = 3


def _build_graph_context_document(state: HybridRagState) -> Dict[str, Any]:
    """Graph DB 계산 결과 자체를 RAG 근거 문서처럼 포장하는 함수입니다."""

    # graph_result:
    # - Graph DB가 이미 계산한 팀 약점, 추천 후보, 분석 카드 정보를 담고 있습니다.
    graph_result = state.get("graph_result", {})
    request_type = state.get("request_type", "analysis")

    if request_type == "recommendation":
        analysis = graph_result.get("analysis", {})
        recommendations = graph_result.get("recommendations", [])
        weak_types = analysis.get("weak_types", [])
        content = (
            "Graph DB 추천 근거: "
            f"주요 약점 타입은 {[item.get('type_name') for item in weak_types[:3]]}이고, "
            f"추천 후보는 {[item.get('name') for item in recommendations[:3]]}입니다."
        )
    else:
        insights = graph_result.get("insights", {})
        weak_types = graph_result.get("weak_types", [])
        content = (
            "Graph DB 팀 분석 근거: "
            f"{insights.get('summary', '')} "
            f"주요 약점 타입은 {[item.get('type_name') for item in weak_types[:3]]}입니다."
        )

    return {
        "source": "graph_result",
        "title": "Graph DB 계산 결과",
        "content": content,
        "score": 1.0,
    }


def _build_status_document(title: str, content: str) -> Dict[str, Any]:
    """벡터 검색을 못 했을 때도 이유를 남기기 위한 상태 문서를 만드는 함수입니다."""

    return {
        "source": "vector_status",
        "title": title,
        "content": content,
        "score": 0.0,
    }


def _get_openai_client() -> Optional[Any]:
    """OpenAI 임베딩 클라이언트를 안전하게 생성하는 함수입니다."""

    # OPENAI_API_KEY:
    # - 없으면 벡터 검색용 query embedding을 만들 수 없으므로 Graph 근거만 사용합니다.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    return OpenAI(api_key=api_key)


def _create_query_embedding(query: str) -> Optional[List[float]]:
    """사용자 팀 상황을 설명하는 검색 문장을 embedding 벡터로 바꾸는 함수입니다."""

    # client:
    # - 기존 vectorizer.py와 같은 방식으로 OpenAI embedding API를 호출합니다.
    client = _get_openai_client()
    if client is None:
        return None

    # response.data[0].embedding:
    # - pgvector의 <=> 연산자로 유사도를 계산할 실제 검색 벡터입니다.
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=query)
    return response.data[0].embedding


def _format_embedding_for_pgvector(embedding: Iterable[float]) -> str:
    """Python list 형태의 embedding을 pgvector가 CAST할 수 있는 문자열로 바꿉니다."""

    # pgvector literal:
    # - 예: [0.01,-0.02,0.03]
    # - SQL에서 CAST(:embedding AS vector) 형태로 사용합니다.
    return "[" + ",".join(str(value) for value in embedding) + "]"


def _normalize_vector_row(row: Any) -> Dict[str, Any]:
    """SQLAlchemy row 객체를 프론트/LLM에서 쓰기 쉬운 dict 문서로 정리합니다."""

    mapping = row._mapping
    return {
        "source": mapping.get("source"),
        "title": mapping.get("title"),
        "content": mapping.get("content"),
        "score": round(float(mapping.get("score") or 0.0), 4),
    }


def _query_vector_documents(sql: str, embedding_literal: str, limit: int) -> List[Dict[str, Any]]:
    """하나의 SQL 검색문을 실행해서 벡터 검색 결과 문서 목록을 가져옵니다."""

    # engine.begin():
    # - 읽기 전용 조회지만 connection 생명주기를 깔끔하게 닫기 위해 context manager를 사용합니다.
    with engine.begin() as connection:
        rows = connection.execute(
            text(sql),
            {
                "embedding": embedding_literal,
                "limit": limit,
            },
        ).fetchall()

    return [_normalize_vector_row(row) for row in rows]


def _search_pokemon_knowledge(embedding_literal: str, limit: int) -> List[Dict[str, Any]]:
    """pokemon_knowledge 테이블에서 선택 팀 설명과 가까운 포켓몬 지식 문서를 찾습니다."""

    sql = """
        SELECT
            'pokemon_knowledge' AS source,
            COALESCE(p.name, CONCAT('pokemon_id=', pk.pokemon_id)) AS title,
            pk.content AS content,
            1 - (pk.embedding <=> CAST(:embedding AS vector)) AS score
        FROM pokemon_knowledge pk
        LEFT JOIN pokemon p ON p.id = pk.pokemon_id
        WHERE pk.embedding IS NOT NULL
        ORDER BY pk.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """
    return _query_vector_documents(sql, embedding_literal, limit)


def _search_flavor_text(embedding_literal: str, limit: int) -> List[Dict[str, Any]]:
    """flavor_text 테이블에서 도감 설명 문장 근거를 찾습니다."""

    sql = """
        SELECT
            'flavor_text' AS source,
            COALESCE(p.name, CONCAT('species_id=', ft.species_id)) AS title,
            ft.content AS content,
            1 - (ft.embedding <=> CAST(:embedding AS vector)) AS score
        FROM flavor_text ft
        LEFT JOIN species s ON s.id = ft.species_id
        LEFT JOIN pokemon p ON p.species_id = s.id
        WHERE ft.embedding IS NOT NULL
        ORDER BY ft.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """
    return _query_vector_documents(sql, embedding_literal, limit)


def _search_abilities(embedding_literal: str, limit: int) -> List[Dict[str, Any]]:
    """abilities 테이블에서 특성 효과 설명 근거를 찾습니다."""

    sql = """
        SELECT
            'abilities' AS source,
            a.name AS title,
            a.effect_text AS content,
            1 - (a.embedding <=> CAST(:embedding AS vector)) AS score
        FROM abilities a
        WHERE a.embedding IS NOT NULL
          AND a.effect_text IS NOT NULL
        ORDER BY a.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """
    return _query_vector_documents(sql, embedding_literal, limit)


def _search_moves(embedding_literal: str, limit: int) -> List[Dict[str, Any]]:
    """moves 테이블에서 기술 효과 설명 근거를 찾습니다."""

    sql = """
        SELECT
            'moves' AS source,
            m.name AS title,
            m.effect_text AS content,
            1 - (m.embedding <=> CAST(:embedding AS vector)) AS score
        FROM moves m
        WHERE m.embedding IS NOT NULL
          AND m.effect_text IS NOT NULL
        ORDER BY m.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """
    return _query_vector_documents(sql, embedding_literal, limit)


def _search_all_vector_tables(embedding: List[float]) -> List[Dict[str, Any]]:
    """RAG 근거로 사용할 여러 벡터 테이블을 검색하고 점수순으로 합칩니다."""

    # embedding_literal:
    # - SQL 파라미터로 넘기기 위해 pgvector 문자열 표현으로 변환한 값입니다.
    embedding_literal = _format_embedding_for_pgvector(embedding)

    # search_functions:
    # - 현재 프로젝트에서 임베딩이 들어갈 가능성이 높은 테이블들을 순서대로 검색합니다.
    search_functions = [
        _search_pokemon_knowledge,
        _search_flavor_text,
        _search_abilities,
        _search_moves,
    ]

    documents: List[Dict[str, Any]] = []
    errors: List[str] = []

    for search_function in search_functions:
        try:
            documents.extend(search_function(embedding_literal, DEFAULT_VECTOR_LIMIT))
        except SQLAlchemyError as exc:
            # 테이블/컬럼이 아직 없거나 embedding이 적재되지 않은 경우에도 전체 RAG는 계속 진행합니다.
            errors.append(f"{search_function.__name__} 실패: {exc.__class__.__name__}")

    # score:
    # - pgvector cosine distance를 1 - distance로 바꾼 값입니다.
    # - 여러 테이블에서 가져온 결과를 한 번 더 정렬해서 관련도가 높은 문서를 위로 올립니다.
    documents = sorted(documents, key=lambda item: item.get("score", 0), reverse=True)

    if errors and not documents:
        documents.append(
            _build_status_document(
                title="Vector DB 검색 실패",
                content="; ".join(errors),
            )
        )

    return documents[:8]


def search_vector_documents(state: HybridRagState) -> Dict[str, List[Dict[str, Any]]]:
    """
    pgvector에서 RAG 근거 문서를 검색하는 LangGraph 노드 함수입니다.

    동작:
        1. Graph DB 계산 결과를 항상 첫 번째 근거로 넣습니다.
        2. vector_query를 embedding으로 바꿉니다.
        3. pokemon_knowledge, flavor_text, abilities, moves에서 유사 문서를 찾습니다.
        4. OpenAI 키나 벡터 테이블 문제가 있어도 API가 죽지 않도록 상태 문서를 남깁니다.
    """

    # documents:
    # - answer_generator가 최종 답변을 만들 때 참고하는 근거 문서 목록입니다.
    documents = [_build_graph_context_document(state)]

    # vector_query:
    # - graph_tools.py에서 Graph 결과를 기반으로 만든 검색 문장입니다.
    vector_query = state.get("vector_query", "").strip()
    if not vector_query:
        documents.append(
            _build_status_document(
                title="Vector DB 검색 생략",
                content="검색 문장이 없어 Graph DB 계산 결과만 사용했습니다.",
            )
        )
        return {"vector_documents": documents}

    try:
        query_embedding = _create_query_embedding(vector_query)
    except Exception as exc:  # pragma: no cover - 외부 API 오류는 환경마다 달라 방어적으로 처리합니다.
        documents.append(
            _build_status_document(
                title="Embedding 생성 실패",
                content=f"OpenAI embedding 생성 중 오류가 발생해 Graph DB 근거만 사용했습니다: {exc.__class__.__name__}",
            )
        )
        return {"vector_documents": documents}

    if query_embedding is None:
        documents.append(
            _build_status_document(
                title="Vector DB 검색 대기",
                content="OPENAI_API_KEY가 없거나 openai 패키지를 사용할 수 없어 Graph DB 근거만 사용했습니다.",
            )
        )
        return {"vector_documents": documents}

    documents.extend(_search_all_vector_tables(query_embedding))
    return {"vector_documents": documents}
