"""
RAGAS 평가 스크립트 - Phase별 RAG 품질 측정
"""
import os
import sys
import json

# Windows에서 shell 리다이렉트(> file.log)가 CP949로 저장되는 문제 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# stdout/stderr 모두 파일로 복사 (버퍼링 문제 방지)
_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ragas_run.log")
_log_file = open(_LOG_PATH, "w", encoding="utf-8", buffering=1)

class _Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            try: s.write(data); s.flush()
            except Exception: pass
    def flush(self):
        for s in self.streams:
            try: s.flush()
            except Exception: pass

sys.stdout = _Tee(sys.__stdout__, _log_file)
sys.stderr = _Tee(sys.__stderr__, _log_file)

# LangSmith 비활성화
os.environ["LANGSMITH_TRACING"]    = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# 경로 설정
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(ROOT), ".env"))

os.environ["LANGSMITH_TRACING"]    = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ.setdefault("GRAPH_DB_URI", "bolt://localhost:7687")
os.environ.setdefault(
    "DATABASE_URL",
    f"postgresql://{os.environ.get('POSTGRES_USER','postgres')}:"
    f"{os.environ.get('POSTGRES_PASSWORD','postgres')}@localhost:5433/"
    f"{os.environ.get('POSTGRES_DB','pokemon_db')}"
)

# ── 테스트셋 ──────────────────────────────────────────────────
TEST_CASES = [
    ("피카츄의 HP, 공격, 방어, 특공, 특방, 스피드 스탯을 알려줘",
     "피카츄의 스탯: HP 35, 공격 55, 방어 40, 특수공격 50, 특수방어 50, 스피드 90"),
    ("공격력이 가장 높은 포켓몬 3마리는 뭐야?",
     "공격력 상위 3위: 메가 뮤츠 X(190), 메가 헤라크로스(185), 종이신도(181)"),
    ("1세대 포켓몬 중에서 포획률이 가장 낮은 포켓몬은?",
     "1세대 전설 포켓몬(프리져, 썬더, 파이어)의 포획률은 3으로 가장 낮다."),
    ("불꽃을 몸에서 뿜어내는 느낌의 포켓몬을 도감 설명 기반으로 추천해줘",
     "리자몽, 마그마, 포챠나 등 불꽃을 몸에서 뿜는 도감 설명을 가진 포켓몬들이 있다."),
    ("잠을 자거나 꿈과 관련된 포켓몬은 어떤 게 있어?",
     "몽나(096), 몽얌나(097), 다크라이(491) 등이 꿈과 관련된 도감 설명을 가지고 있다."),
    ("이브이는 어떤 포켓몬으로 진화해?",
     "이브이는 샤미드(물의돌), 부스터(불꽃의돌), 쥬피썬더(천둥의돌), 에스피온(낮 친밀도), 블래키(밤 친밀도), 리피아(이끼의돌), 글레이시아(얼음의돌), 님피아(요정의돌)로 진화한다."),
    ("꼬부기의 최종 진화는 뭐야?",
     "꼬부기 → 어니부기(Lv.16) → 거북왕(Lv.36)으로 진화한다."),
    ("드래곤 타입의 약점은 뭐야?",
     "드래곤 타입은 드래곤(2배), 얼음(2배), 페어리(2배) 타입 공격에 약하다."),
    ("강철 타입은 어떤 타입 공격에 저항이 있어?",
     "강철 타입은 독(무효), 노말(0.5배), 페어리(0.5배), 드래곤(0.5배), 에스퍼(0.5배) 등 많은 타입에 저항한다."),
    ("피카츄의 스탯과 약점 타입을 함께 알려줘",
     "피카츄: HP 35, 공격 55, 방어 40, 특공 50, 특방 50, 스피드 90. 전기 타입이므로 땅 타입(2배)에 약하다."),
]

print(f"테스트 케이스 {len(TEST_CASES)}개 준비 완료\n")

# ── 에이전트 로드 ─────────────────────────────────────────────
print("챗봇 에이전트 로딩 중...")
from chatbot.pokemon_agent import get_agent
from langchain_core.messages import HumanMessage, ToolMessage
print("에이전트 로딩 완료\n")

def run_and_collect(question: str, model: str = "gpt-4o-mini") -> dict:
    agent = get_agent(model)
    result = agent.invoke({
        "messages": [HumanMessage(content=question)],
        "tool_call_count": 0,
    })
    contexts = [
        msg.content for msg in result["messages"]
        if isinstance(msg, ToolMessage)
        and msg.content
        and "오류" not in msg.content[:10]
    ]
    return {"answer": result["messages"][-1].content, "contexts": contexts}

# ── RAGAS 평가 ───────────────────────────────────────────────
print("=" * 60)
print("RAGAS 평가 시작")
print("=" * 60)

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    faithfulness, answer_relevancy,
    LLMContextRecall, LLMContextPrecisionWithReference,
)
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))

samples, results_raw = [], []

for i, (question, ground_truth) in enumerate(TEST_CASES, 1):
    print(f"\n[{i:02d}/{len(TEST_CASES)}] {question[:50]}...")
    try:
        collected = run_and_collect(question)
        answer    = collected["answer"]
        contexts  = collected["contexts"] or ["(검색 결과 없음)"]
        print(f"       컨텍스트 수: {len(contexts)}, 답변 길이: {len(answer)}자")
        samples.append(SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=contexts,
            reference=ground_truth,
        ))
        results_raw.append({"question": question, "answer": answer,
                            "contexts_count": len(contexts), "ground_truth": ground_truth})
    except Exception as e:
        print(f"       오류: {e}")

print(f"\n{len(samples)}개 샘플 수집 완료. RAGAS 평가 중...\n")

score = evaluate(
    dataset=EvaluationDataset(samples=samples),
    metrics=[
        faithfulness,
        answer_relevancy,
        LLMContextRecall(llm=evaluator_llm),
        LLMContextPrecisionWithReference(llm=evaluator_llm),
    ],
    llm=evaluator_llm,
)

df = score.to_pandas()
metric_cols = [c for c in df.columns if c not in
               ("user_input", "response", "retrieved_contexts", "reference")]

print("\n" + "=" * 60)
print("RAGAS 결과 요약")
print("=" * 60)
for col in metric_cols:
    val = df[col].mean()
    bar = "█" * int(val * 20) + "░" * (20 - int(val * 20))
    print(f"  {col:<42} {bar}  {val:.4f}")

out_path = os.path.join(os.path.dirname(__file__), "ragas_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "summary": {col: float(df[col].mean()) for col in metric_cols},
        "details": results_raw,
    }, f, ensure_ascii=False, indent=2)

print(f"\n결과 저장: {out_path}")
