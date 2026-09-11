from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.config import settings
from src.nodes import (
    AgentState,
    execute_node,
    finalize_node,
    generate_sql_node,
    link_schema_node,
    reflect_node,
    retrieve_memory_node,
    retrieve_playbook_node,
)


def route_after_execute(state: AgentState) -> str:
    error = (state.get("error") or "").strip()
    retries = int(state.get("retries") or 0)
    mode = state.get("mode") or "C"
    max_retries = 0 if mode == "A" else settings.max_retries
    if error and retries < max_retries:
        return "reflect"
    return "finalize"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("link_schema", link_schema_node)
    g.add_node("retrieve_memory", retrieve_memory_node)
    g.add_node("retrieve_playbook", retrieve_playbook_node)
    g.add_node("generate_sql", generate_sql_node)
    g.add_node("execute", execute_node)
    g.add_node("reflect", reflect_node)
    g.add_node("finalize", finalize_node)
    g.set_entry_point("link_schema")
    g.add_edge("link_schema", "retrieve_memory")
    g.add_edge("retrieve_memory", "retrieve_playbook")
    g.add_edge("retrieve_playbook", "generate_sql")
    g.add_edge("generate_sql", "execute")
    g.add_conditional_edges(
        "execute",
        route_after_execute,
        {"reflect": "reflect", "finalize": "finalize"},
    )
    g.add_edge("reflect", "generate_sql")
    g.add_edge("finalize", END)
    return g.compile()


graph = build_graph()


def run_question(question: str, mode: str = "C", user_id: str | None = None) -> AgentState:
    return graph.invoke(
        {
            "question": question,
            "mode": mode,
            "user_id": user_id or settings.agent_user_id,
            "retries": 0,
            "reflections": [],
            "error": "",
            "rows": [],
            "columns": [],
        }
    )
