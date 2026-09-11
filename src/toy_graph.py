"""Minimal LangGraph example: question -> echo -> END."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph


class ToyState(TypedDict):
    question: str
    echo: str


def echo_node(state: ToyState) -> dict:
    return {"echo": f"got: {state['question']}"}


def build_toy():
    g = StateGraph(ToyState)
    g.add_node("echo", echo_node)
    g.set_entry_point("echo")
    g.add_edge("echo", END)
    return g.compile()


def main() -> None:
    result = build_toy().invoke({"question": "how many artists?"})
    print(result)


if __name__ == "__main__":
    main()
