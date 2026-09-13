"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPFridgeServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPFridgeServer, verbose: bool = True) -> list:
    """Run multi-step ReAct loop with OpenAI-compatible tool messages."""
    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    messages = [{"role": "user", "content": user_query}]
    trace_logs = []
    tools_list = mcp_server.list_tools()

    for step in range(1, MAX_ITERATIONS + 1):
        step_start_time = time.time()
        if verbose:
            print(f"\n--- 🔄 ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        llm_response = provider.generate_with_tools(messages, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        thought = llm_response.get("thought", "Đang suy luận...")
        if verbose:
            print(f"🧠 [Thought]: {thought}")

        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            if verbose:
                print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({"step": step, "query": user_query, "action_type": "FINAL_ANSWER", "thought": thought, "output": final_content, "latency_ms": latency_ms})
            return trace_logs

        if llm_response.get("type") != "tool_call":
            final_content = "Không nhận được phản hồi hợp lệ từ LLM."
            if verbose:
                print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({"step": step, "query": user_query, "action_type": "FINAL_ANSWER", "thought": thought, "output": final_content, "latency_ms": latency_ms})
            return trace_logs

        tool_name = llm_response.get("tool_name")
        arguments = llm_response.get("arguments", {})
        call_id = llm_response.get("tool_call_id") or f"call_{step}"
        if verbose:
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

        assistant_message = llm_response.get("assistant_message") or {"role": "assistant", "content": None, "tool_calls": [{"id": call_id, "type": "function", "function": {"name": tool_name, "arguments": json.dumps(arguments, ensure_ascii=False)}}]}
        messages.append(assistant_message)

        mcp_result = mcp_server.call_tool(tool_name, arguments)
        obs_data = mcp_result.get("result", {})
        obs_str = json.dumps(obs_data, ensure_ascii=False)
        if verbose:
            print(f"👁️ [Observation từ MCP Server]: {obs_str}")
        messages.append({"role": "tool", "tool_call_id": call_id, "name": tool_name, "content": obs_str})
        trace_logs.append({"step": step, "query": user_query, "action_type": "TOOL_EXECUTION", "tool_name": tool_name, "arguments": arguments, "observation": obs_data, "latency_ms": latency_ms})

    final_content = "Đã chạm giới hạn vòng lặp, dừng an toàn."
    if verbose:
        print(f"🏁 [Final Answer]: {final_content}")
    trace_logs.append({"step": MAX_ITERATIONS, "query": user_query, "action_type": "FINAL_ANSWER", "thought": "MAX_ITERATIONS reached", "output": final_content, "latency_ms": 0})
    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🥬 SMART FRIDGE FOOD-WASTE RESCUE AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPFridgeServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Capability: 'Bạn có thể giúp giảm lãng phí thực phẩm như thế nào?'")
        print("   - Inventory: 'Kiểm tra tủ lạnh USER001 có gì sắp hết hạn?'")
        print("   - Meal plan: 'Tạo meal plan bữa tối cho USER001 ưu tiên món sắp hết hạn'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Người dùng hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (Smart Fridge) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
