"""
Answer generator for Team Build Hybrid RAG.

목적:
    Hybrid RAG의 마지막 단계에서 Graph DB 계산 결과와 Vector DB 검색 근거를 LLM 프롬프트로 묶고,
    LLM이 실제 사용자용 자연어 답변을 생성하도록 합니다.

중요:
    generate_answer()가 {"final_answer": "..."} 형태로 반환하는 이유는
    LangGraph 노드가 "상태에 추가할 값"을 dict로 반환해야 하기 때문입니다.
    즉, 이 dict는 사용자에게 보여주는 최종 응답 포맷이 아니라 LangGraph 내부 상태 업데이트 포맷입니다.
"""

import json
import os
from typing import Any, Dict, List, Optional

import requests

from team_build_rag.scoring_policy import get_answer_generation_weights
from team_build_rag.state import HybridRagState, get_request_type


def _safe_json(data: Any) -> str:
    """프롬프트에 넣을 데이터를 깨지지 않는 JSON 문자열로 바꾸는 함수입니다."""

    # ensure_ascii=False:
    # - 포켓몬 이름과 타입 이름이 한국어이므로 그대로 보이게 하기 위한 옵션입니다.
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _get_huggingface_config() -> Optional[Dict[str, Any]]:
    """Hugging Face Router 호출에 필요한 설정을 읽는 함수입니다."""

    # hf_token:
    # - Hugging Face Inference Providers를 호출하기 위한 토큰입니다.
    # - OPENAI_API_KEY는 사용하지 않고, HF_TOKEN 또는 HUGGINGFACEHUB_API_TOKEN만 읽습니다.
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        return None

    # model:
    # - 기본 모델은 Hugging Face Router에서 비교적 안정적으로 잡히는 Qwen2.5-7B-Instruct입니다.
    # - :fastest는 Hugging Face Router가 사용 가능한 provider 중 빠른 쪽을 고르게 하는 옵션입니다.
    model = os.getenv("TEAM_BUILD_RAG_HF_MODEL", "Qwen/Qwen2.5-7B-Instruct:fastest")

    return {
        "endpoint": os.getenv(
            "TEAM_BUILD_RAG_HF_ENDPOINT",
            "https://router.huggingface.co/v1/chat/completions",
        ),
        "model": model,
        "token": hf_token,
        "temperature": float(os.getenv("TEAM_BUILD_RAG_TEMPERATURE", "0.2")),
        "max_tokens": int(os.getenv("TEAM_BUILD_RAG_MAX_TOKENS", "900")),
        "timeout": int(os.getenv("TEAM_BUILD_RAG_TIMEOUT", "60")),
    }


def _build_evidence_context(state: HybridRagState) -> str:
    """Vector DB 검색 근거 문서를 LLM 프롬프트용 텍스트로 정리하는 함수입니다."""

    # vector_documents:
    # - vector_search.py에서 Graph 결과 문서와 pgvector 검색 문서를 합쳐 넣어둔 근거 목록입니다.
    documents = state.get("vector_documents", [])
    if not documents:
        return "검색 근거 문서가 없습니다. Graph DB 계산 결과를 중심으로 답변하세요."

    evidence_blocks: List[str] = []
    for index, document in enumerate(documents[:8], start=1):
        evidence_blocks.append(
            "\n".join(
                [
                    f"[근거 {index}]",
                    f"source: {document.get('source', 'unknown')}",
                    f"title: {document.get('title', '제목 없음')}",
                    f"score: {document.get('score', 0)}",
                    f"content: {document.get('content', '')}",
                ]
            )
        )

    return "\n\n".join(evidence_blocks)


def _build_analysis_prompt(state: HybridRagState, graph_result: Dict[str, Any]) -> str:
    """덱 분석 요청용 RAG 프롬프트를 만드는 함수입니다."""

    # answer_weights:
    # - 답변 생성 단계에서 Graph 계산 근거와 Vector 문서 근거를 어떤 비중으로 설명할지 나타냅니다.
    answer_weights = get_answer_generation_weights()

    # compact_graph_result:
    # - LLM이 필요한 핵심 정보만 읽을 수 있도록 Graph 결과를 그대로 넣되, 역할을 명확히 지시합니다.
    compact_graph_result = {
        "selected_pokemon": graph_result.get("selected_pokemon", []),
        "weak_types": graph_result.get("weak_types", []),
        "resistant_types": graph_result.get("resistant_types", []),
        "move_type_coverage": graph_result.get("move_type_coverage", []),
        "insights": graph_result.get("insights", {}),
        "answer_policy": answer_weights,
    }

    return f"""
너는 포켓몬 팀 빌딩을 도와주는 분석가다.
아래 Graph DB 계산 결과와 검색 근거를 사용해서 사용자가 선택한 5마리 덱을 분석해라.

답변 규칙:
- 한국어로 답변한다.
- 첫 문단은 반드시 "결론:"으로 시작하고, 현재 덱의 핵심 판단과 6번째 포켓몬 방향을 2~3문장으로 먼저 요약한다.
- 두 번째 문단부터 약점, 방어 안정성, 기술 커버리지 근거를 설명한다.
- 단순 나열이 아니라 "왜 그런 판단을 했는지" 설명한다.
- 약점 타입, 안정적인 방어 타입, 기술 타입 커버리지, 6번째 포켓몬 방향을 포함한다.
- 답변 설명 비중은 Graph DB 계산 근거 {answer_weights["graph"]:.0%}, Vector DB 검색 근거 {answer_weights["vector"]:.0%}로 둔다.
- 단, 타입 배율/점수처럼 숫자로 계산된 값은 Graph DB 또는 hybrid_score 결과를 우선 신뢰한다.
- 숫자는 Graph DB 결과를 우선 신뢰한다.
- 근거에 없는 내용을 확정적으로 지어내지 않는다.
- 너무 길게 늘어놓지 말고 4~6문단 정도로 정리한다.
- 문단 사이에는 빈 줄을 넣어 화면에서 첫 결론과 세부 설명이 분리되게 한다.

[Graph DB 계산 결과]
{_safe_json(compact_graph_result)}

[검색 근거]
{_build_evidence_context(state)}

최종 답변:
""".strip()


def _build_recommendation_prompt(state: HybridRagState, reranked_result: Dict[str, Any]) -> str:
    """추천 요청용 RAG 프롬프트를 만드는 함수입니다."""

    # answer_weights:
    # - 추천 순위는 hybrid_scorer가 정하고, 여기서는 AI 해설의 근거 반영 비중을 명시합니다.
    answer_weights = get_answer_generation_weights()

    # compact_reranked_result:
    # - 추천 후보, 점수, 이유, 기존 팀 분석 결과를 LLM에게 같이 제공합니다.
    compact_reranked_result = {
        "analysis": reranked_result.get("analysis", {}),
        "recommendations": reranked_result.get("recommendations", []),
        "hybrid_policy": reranked_result.get("hybrid_policy", {}),
        "answer_policy": answer_weights,
    }

    return f"""
너는 포켓몬 팀 빌딩을 도와주는 추천 분석가다.
아래 Graph DB 추천 결과와 검색 근거를 사용해서 6번째 포켓몬 추천 이유를 설명해라.

답변 규칙:
- 한국어로 답변한다.
- 첫 문단은 반드시 "결론:"으로 시작하고, 1순위 추천 포켓몬과 추천 이유를 2~3문장으로 먼저 요약한다.
- 두 번째 문단부터 약점 보완 관계, 대표 기술 활용, 2~3순위 비교를 설명한다.
- 1순위 추천 포켓몬을 가장 먼저 말한다.
- "몇 개 약점 보완"처럼 뭉뚱그리지 말고, 어떤 약점 타입을 어떤 저항/무효 관계로 보완하는지 구체적으로 말한다.
- useful_moves에 있는 기술명을 반드시 활용해서, 어떤 기술이 주력기인지/견제기인지/어떤 상황에서 쓸지 설명한다.
- 추천 점수, 보완하는 약점, 대표 기술, 기대 역할을 설명한다.
- 답변 설명 비중은 Graph DB 계산 근거 {answer_weights["graph"]:.0%}, Vector DB 검색 근거 {answer_weights["vector"]:.0%}로 둔다.
- 단, 추천 순위와 최종 점수는 hybrid_score를 우선 신뢰한다.
- 2~3순위 후보가 있으면 비교 관점으로 짧게 언급한다.
- 숫자와 추천 순위는 Graph DB 결과를 우선 신뢰한다.
- 근거에 없는 내용을 확정적으로 지어내지 않는다.
- 사용자가 바로 선택을 판단할 수 있도록 5~7문단 정도로 정리한다.
- 문단 사이에는 빈 줄을 넣어 화면에서 첫 결론과 세부 설명이 분리되게 한다.
- 문장 예시: "디아루가는 바위 공격을 0.5배로 받아 리자몽/피죤투 쪽의 부담을 줄이고, 용성군은 드래곤 상대로 강하게 압박할 때 유용합니다."

[Graph DB 추천 결과]
{_safe_json(compact_reranked_result)}

[검색 근거]
{_build_evidence_context(state)}

최종 답변:
""".strip()


def _call_llm(prompt: str) -> str:
    """LLM을 호출해서 RAG 답변을 생성하는 함수입니다."""

    # config:
    # - Hugging Face Router를 통해 Qwen2.5-7B-Instruct를 호출하기 위한 설정입니다.
    # - 토큰이 없으면 조용히 넘어가지 않고, 화면에서 바로 원인을 알 수 있도록 에러를 냅니다.
    config = _get_huggingface_config()
    if config is None:
        raise RuntimeError(
            "Hugging Face 토큰이 설정되지 않았습니다. .env에 HF_TOKEN 또는 HUGGINGFACEHUB_API_TOKEN을 넣어 주세요."
        )

    try:
        # payload:
        # - Hugging Face Router의 chat completions 형식에 맞춘 요청 본문입니다.
        # - messages 안의 user content에 RAG 프롬프트 전체를 넣어 답변을 생성합니다.
        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
        }

        # response:
        # - requests를 직접 쓰면 langchain-openai/openai 패키지에 의존하지 않고 HF만 사용할 수 있습니다.
        response = requests.post(
            config["endpoint"],
            headers={
                "Authorization": f"Bearer {config['token']}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=config["timeout"],
        )
        response.raise_for_status()
        data = response.json()

        # content:
        # - OpenAI-compatible 응답 구조에서 실제 AI 답변 텍스트만 꺼냅니다.
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise RuntimeError("LLM API 응답에 content가 없습니다.")
        return str(content).strip()
    except Exception as exc:
        # 대체 답변을 쓰면 API 키/모델/네트워크 문제가 화면에서 숨겨질 수 있으므로 그대로 실패시킵니다.
        raise RuntimeError(f"Hugging Face Qwen 호출에 실패했습니다: {exc}") from exc


def generate_answer(state: HybridRagState) -> Dict[str, str]:
    """LangGraph 워크플로우의 최종 답변을 생성하는 노드 함수입니다."""

    # request_type:
    # - analysis면 덱 분석 RAG 프롬프트, recommendation이면 추천 RAG 프롬프트를 사용합니다.
    request_type = get_request_type(state)

    # result:
    # - recommendation은 hybrid_scorer를 거친 reranked_result를 우선 사용합니다.
    # - analysis는 graph_result가 그대로 최종 분석 결과입니다.
    result = state.get("reranked_result", state.get("graph_result", {}))

    if request_type == "recommendation":
        prompt = _build_recommendation_prompt(state, result)
        return {"final_answer": _call_llm(prompt)}

    prompt = _build_analysis_prompt(state, result)
    return {"final_answer": _call_llm(prompt)}
