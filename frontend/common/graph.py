# graph.py
from langgraph.graph import StateGraph, END
from nodes import (
    PokemonChatState,
    router_node,
    sql_node,
    general_node,
    quality_check,
    answer_node
)

def build_graph():
    graph = StateGraph(PokemonChatState)

    # ── 노드 등록 ──────────────────────
    graph.add_node("router",  router_node)
    graph.add_node("sql",     sql_node)
    graph.add_node("general", general_node)
    graph.add_node("answer",  answer_node)

    # ── 시작점 ─────────────────────────
    graph.set_entry_point("router")

    # ── 라우터 → 검색 노드 ─────────────
    graph.add_conditional_edges(
        "router",
        lambda state: state["intent"],
        {
            "sql"     : "sql",
            "general" : "general"
        }
    )

    # ── 검색 → 품질 체크 ───────────────
    graph.add_conditional_edges(
        "sql",
        quality_check,
        {
            "retry"  : "router",
            "answer" : "answer"
        }
    )
    graph.add_conditional_edges(
        "general",
        quality_check,
        {
            "retry"  : "router",
            "answer" : "answer"
        }
    )

    # ── 답변 → 종료 ────────────────────
    graph.add_edge("answer", END)

    return graph.compile()

# 그래프 인스턴스 (싱글톤)
app = build_graph()

# ── 그래프 시각화 ──────────────────────
def save_graph_image(filename="pokemon_graph.png"):
    png_data = app.get_graph().draw_mermaid_png()
    with open(filename, "wb") as f:
        f.write(png_data)
    print(f"그래프 저장 완료 → {filename}")

if __name__ == "__main__":
    save_graph_image()