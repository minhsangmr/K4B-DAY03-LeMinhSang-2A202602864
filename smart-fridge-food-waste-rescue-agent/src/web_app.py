"""Streamlit live demo for Smart Fridge Food-Waste Rescue Agent."""

import json
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent
from mcp_server import MCPFridgeServer
from providers import get_llm_provider


TRACE_PATH = Path(__file__).resolve().parents[1] / "docs" / "trace_waterfall.json"
DEFAULT_PROMPT = "Tối nay USER001 muốn ăn món ít calo. Hãy kiểm tra tủ lạnh, ưu tiên thực phẩm sắp hết hạn, rồi tạo meal plan và shopping list cho những nguyên liệu còn thiếu."


def final_answer(trace):
    for event in reversed(trace):
        if event.get("action_type") == "FINAL_ANSWER":
            return event.get("output", "")
    return "Không có final answer."


def save_trace(trace):
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACE_PATH.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")


def render_trace(trace):
    for event in trace:
        with st.expander(f"Step {event.get('step')} — {event.get('action_type')}", expanded=True):
            if event.get("thought"):
                st.markdown(f"**Decision Summary:** {event['thought']}")
            if event.get("tool_name"):
                st.markdown(f"**Action:** `{event['tool_name']}`")
                st.json(event.get("arguments", {}))
                st.markdown("**Observation:**")
                st.json(event.get("observation", {}))
            else:
                st.markdown("**Final Answer:**")
                st.write(event.get("output", ""))
            st.caption(f"Latency: {event.get('latency_ms')} ms")


def main():
    st.set_page_config(page_title="Smart Fridge Food-Waste Rescue Agent", page_icon="🥬")
    st.title("🥬 Smart Fridge Food-Waste Rescue Agent")
    st.caption("ReAct + MCP tools: fridge_query, create_food_plan")

    if "provider" not in st.session_state:
        st.session_state.provider = get_llm_provider()
        st.session_state.mcp_server = MCPFridgeServer()
        st.session_state.messages = []
        st.session_state.last_trace = []

    provider = st.session_state.provider
    mcp_server = st.session_state.mcp_server

    st.sidebar.markdown(f"**Provider:** `{provider.__class__.__name__}`")
    st.sidebar.markdown(f"**Model:** `{getattr(provider, 'model_name', 'unknown')}`")
    st.sidebar.markdown(f"**MCP Server:** `{mcp_server.server_name}`")
    user_id = st.sidebar.text_input("User ID", "USER001").strip().upper()
    if st.sidebar.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.last_trace = []
        st.rerun()

    st.info("Không hiển thị API key/base URL. Dữ liệu inventory chỉ lấy qua MCP tool.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Nhập yêu cầu", key="chat_input")
    if st.button("Run TC04 demo prompt"):
        prompt = DEFAULT_PROMPT
    if prompt:
        if "USER" not in prompt.upper():
            prompt = f"{prompt} User ID: {user_id}"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            trace = run_react_agent(prompt, provider, mcp_server, verbose=False)
            answer = final_answer(trace)
            save_trace(trace)
            st.session_state.last_trace = trace
        except Exception as exc:
            answer = f"Lỗi khi chạy agent: {exc}"
            trace = []

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

    if st.session_state.last_trace:
        st.subheader("Waterfall Trace")
        render_trace(st.session_state.last_trace)


if __name__ == "__main__":
    main()
