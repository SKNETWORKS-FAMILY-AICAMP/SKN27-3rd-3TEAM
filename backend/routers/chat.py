from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"],
)

class RapBattleRequest(BaseModel):
    pokemon1: str
    pokemon2: str

class RapBattleResponse(BaseModel):
    script: str

SYSTEM_PROMPT = (
    "너는 포켓몬 세계의 힙합 프로듀서이자 랩 배틀 심사위원이야. "
    "사용자가 선택한 두 마리의 포켓몬이 서로의 타입 약점, 도감 설정, 외모, 기술 등을 활용해 "
    "매우 찰지고 유머러스한 랩 배틀(디스전)을 하도록 대본을 써줘. "
    "각 포켓몬은 2~3마디씩 번갈아가며 공격하고, 마지막에는 심사평과 함께 승자를 '🏆 승자: [포켓몬이름]' 형식으로 발표해줘. "
    "한국어 힙합 느낌(쇼미더머니 스타일)으로 작성해줘."
)

OPENAI_TIMEOUT = 60  # OpenAI API 호출 타임아웃 (초)

def _make_llm(streaming: bool = False):
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.8,
        streaming=streaming,
        api_key=os.getenv("OPENAI_API_KEY"),
        request_timeout=OPENAI_TIMEOUT,
    )

def _build_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "{p1} vs {p2}의 영혼의 디스전을 시작해줘!")
    ])

@router.post("/rap-battle", response_model=RapBattleResponse)
async def generate_rap_battle(request: RapBattleRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")
    chain = _build_prompt() | _make_llm()
    try:
        response = await asyncio.wait_for(
            chain.ainvoke({"p1": request.pokemon1, "p2": request.pokemon2}),
            timeout=OPENAI_TIMEOUT,
        )
        return RapBattleResponse(script=response.content)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="OpenAI API 응답 시간 초과")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rap-battle/stream")
async def stream_rap_battle(request: RapBattleRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        def no_key():
            yield "[오류] OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        return StreamingResponse(no_key(), media_type="text/plain; charset=utf-8")

    # 동기 generator: FastAPI가 스레드풀에서 실행하므로 이벤트루프 간섭 없음
    def sync_generate():
        llm = _make_llm(streaming=True)
        chain = _build_prompt() | llm
        try:
            logger.info("Rap battle stream started: %s vs %s", request.pokemon1, request.pokemon2)
            for chunk in chain.stream({"p1": request.pokemon1, "p2": request.pokemon2}):
                if chunk.content:
                    yield chunk.content
            logger.info("Rap battle stream completed")
        except Exception as e:
            logger.error("Rap battle stream error: %s", e)
            yield f"\n\n[오류: {str(e)}]"

    return StreamingResponse(sync_generate(), media_type="text/plain; charset=utf-8")
