"""
Hybrid retriever for Graph + Vector RAG.

목적:
    Graph DB 결과와 Vector DB 검색 결과를 LLM이 읽기 쉬운 근거 패키지로 합칩니다.
    이 단계는 "정확한 계산 근거"와 "설명용 텍스트 근거"를 하나로 묶는 역할을 합니다.
"""

from typing import Any, Dict, List

from team_build_rag.state import HybridRagState


def build_hybrid_context(state: HybridRagState) -> Dict[str, Any]:
    """Graph 결과와 Vector 문서를 하나의 context로 정리하는 함수입니다."""

    # graph_result:
    # - Neo4j 기반의 정량 분석/추천 결과입니다.
    graph_result = state.get("graph_result", {})

    # vector_documents:
    # - Vector DB 또는 placeholder 검색에서 가져온 설명 근거입니다.
    vector_documents = state.get("vector_documents", [])

    return {
        "llm_evaluation": {
            "graph_result": graph_result,
            "evidence_documents": vector_documents,
            "evidence_count": len(vector_documents),
            "notes": [
                "Graph DB 결과를 1차 근거로 사용합니다.",
                "Vector DB 문서는 설명을 풍부하게 만드는 보조 근거로 사용합니다.",
            ],
        }
    }
