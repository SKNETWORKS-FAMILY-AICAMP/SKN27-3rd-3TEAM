"""Vector evidence scorer for Team Build Hybrid RAG.

목적:
    Vector DB에서 가져온 문서가 특정 추천 후보나 덱 분석 결과를 얼마나 잘 뒷받침하는지 계산합니다.
    이 파일은 "벡터 검색" 자체가 아니라, 검색된 문서를 점수화하는 역할만 담당합니다.
"""

from typing import Any, Dict, Iterable, List

from team_build_rag.scoring_policy import normalize_vector_score


def _as_text(value: Any) -> str:
    """검색어 비교를 위해 None, 숫자, 문자열을 안전하게 문자열로 바꿉니다."""

    return str(value or "").strip().lower()


def _document_text(document: Dict[str, Any]) -> str:
    """문서 제목과 본문을 합쳐 후보 매칭용 문자열을 만듭니다."""

    return f"{document.get('title', '')} {document.get('content', '')}".lower()


def _collect_candidate_terms(candidate: Dict[str, Any]) -> List[str]:
    """추천 후보 1마리와 관련된 이름/타입/기술 키워드를 모읍니다."""

    terms = [_as_text(candidate.get("name"))]

    # pokemon_types:
    # - 후보 자신의 타입입니다. 예: 강철/에스퍼 타입 후보라면 이 타입 설명 문서가 근거가 됩니다.
    for type_item in candidate.get("pokemon_types", []) or candidate.get("types", []):
        terms.append(_as_text(type_item.get("type_name")))

    # defensive_covers:
    # - 현재 팀 약점을 어떤 타입 저항/무효로 보완하는지 판단할 때 쓰는 타입입니다.
    for cover in candidate.get("defensive_covers", []):
        terms.append(_as_text(cover.get("type_name")))

    # useful_moves:
    # - 추천 이유에 가장 직접적으로 쓰이는 기술명과 기술 타입입니다.
    for move in candidate.get("useful_moves", []):
        terms.append(_as_text(move.get("move_name")))
        terms.append(_as_text(move.get("type_name")))

    return [term for term in terms if term]


def _match_documents(terms: Iterable[str], documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """키워드가 문서에 포함되는지 확인해서 후보와 관련 있는 Vector 문서만 골라냅니다."""

    matched_documents: List[Dict[str, Any]] = []
    for document in documents:
        text = _document_text(document)
        if any(term and term in text for term in terms):
            matched_documents.append(document)

    return sorted(
        matched_documents,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )


def _score_documents(documents: List[Dict[str, Any]]) -> float:
    """매칭된 문서들의 유사도를 0~100 점수로 요약합니다."""

    if not documents:
        return 0.0

    # top_documents:
    # - 모든 문서를 평균내면 약한 근거가 점수를 희석시킬 수 있어 상위 3개만 사용합니다.
    top_documents = documents[:3]
    average_score = sum(float(item.get("score") or 0) for item in top_documents) / len(top_documents)
    return normalize_vector_score(average_score)


def score_recommendation_evidence(
    recommendations: List[Dict[str, Any]],
    vector_documents: List[Dict[str, Any]],
) -> Dict[int, Dict[str, Any]]:
    """추천 후보별 Vector 근거 점수를 계산합니다."""

    score_map: Dict[int, Dict[str, Any]] = {}
    for candidate in recommendations:
        pokemon_id = int(candidate.get("pokemon_id"))
        terms = _collect_candidate_terms(candidate)
        matched_documents = _match_documents(terms, vector_documents)

        score_map[pokemon_id] = {
            "vector_score": _score_documents(matched_documents),
            "vector_evidence": matched_documents[:3],
            "matched_terms": terms[:12],
        }

    return score_map


def score_analysis_evidence(
    graph_result: Dict[str, Any],
    vector_documents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """덱 분석 결과 전체에 대한 Vector 근거 점수를 계산합니다."""

    terms: List[str] = []

    # selected_pokemon:
    # - 사용자가 고른 5마리 이름이 문서에 잡히면 분석 설명의 근거로 사용할 수 있습니다.
    for pokemon in graph_result.get("selected_pokemon", []):
        terms.append(_as_text(pokemon.get("name")))
        for type_item in pokemon.get("types", []):
            terms.append(_as_text(type_item.get("type_name")))

    # weak/resistant types:
    # - 덱 분석에서 가장 중요한 약점/저항 타입을 문서 근거와 연결합니다.
    for group_name in ("weak_types", "resistant_types"):
        for type_item in graph_result.get(group_name, []):
            terms.append(_as_text(type_item.get("type_name")))

    matched_documents = _match_documents([term for term in terms if term], vector_documents)
    return {
        "vector_score": _score_documents(matched_documents),
        "vector_evidence": matched_documents[:5],
        "matched_terms": terms[:20],
    }
