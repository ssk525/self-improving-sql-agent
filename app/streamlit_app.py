import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from src.db import init_database
from src.graph import run_question
from src import playbook, memory
from src.config import settings

st.set_page_config(page_title="Self-Improving SQL Agent", layout="wide")
st.title("Self-Improving SQL Analyst")
st.caption("LangGraph Text-to-SQL with a playbook that grows from failed queries. Not a RAG chatbot.")

if "db_ready" not in st.session_state:
    init_database()
    st.session_state.db_ready = True

left, right = st.columns([1.2, 1])

with left:
    question = st.text_area(
        "Question",
        value="Who are the top 3 customers by total spend?",
        height=80,
    )
    mode = st.selectbox("Mode", ["C", "B", "A"], help="A=one-shot, B=retry, C=retry+playbook+memory")
    if st.button("Run", type="primary"):
        with st.spinner("Running agent..."):
            state = run_question(question, mode=mode)
        st.session_state.last = state

    state = st.session_state.get("last")
    if state:
        st.subheader("SQL")
        st.code(state.get("sql") or "", language="sql")
        if state.get("error"):
            st.error(state["error"])
        cols = state.get("columns") or []
        rows = state.get("rows") or []
        if cols:
            st.subheader("Result")
            st.dataframe([dict(zip(cols, row)) for row in rows])
        if state.get("reflections"):
            st.subheader("Reflections")
            for r in state["reflections"]:
                st.write(f"- {r}")

with right:
    st.subheader("Playbook")
    bullets = playbook.all_bullets()
    if not bullets:
        st.write("Empty. Failures in mode C write lessons here.")
    for b in bullets:
        cols = st.columns([4, 1])
        cols[0].write(f"{b['text']} (helpful={b['helpful']}, harmful={b['harmful']})")
        if cols[1].button("Delete", key=f"del-{b['id']}"):
            playbook.delete_bullet(b["id"])
            st.rerun()
    st.subheader("User memory")
    mems = memory.all_for_user(settings.agent_user_id)
    if not mems:
        st.write("No stored memories yet.")
    for m in mems:
        st.write(f"- {m}")
