"""OpenAI-compatible and offline mock providers for Smart Fridge."""

import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

class BaseLLMProvider:
    model_name = "base"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    model_name = "MockOfflineProvider-SmartFridge-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return "Tôi có thể tra cứu inventory, phát hiện món sắp hết hạn và tạo meal plan chống lãng phí khi có tool."

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        user_query = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
        query_lower = user_query.lower()
        tool_messages = [m for m in messages if m.get("role") == "tool"]

        if not tool_messages:
            if any(token in query_lower for token in ["kiểm tra", "inventory", "hiện có", "sắp hết hạn", "meal plan", "kế hoạch", "bữa tối", "shopping list"]):
                user_id = "USER999" if "user999" in query_lower else "USER001"
                return self._tool_call("call_1", "fridge_query", {"user_id": user_id}, "Cần tra cứu inventory trước khi trả lời.")
            return {"type": "text", "content": self.generate(user_query), "thought": "Câu hỏi capability chung; không cần gọi tool."}

        observation = json.loads(tool_messages[-1].get("content") or "{}")
        last_tool = tool_messages[-1].get("name")
        if last_tool == "fridge_query" and observation.get("status") == "NOT_FOUND":
            return {"type": "text", "content": observation.get("message", "Không tìm thấy inventory."), "thought": "Inventory không tồn tại; dừng để tránh bịa dữ liệu."}
        if last_tool == "fridge_query" and any(token in query_lower for token in ["tạo", "lập", "meal plan", "kế hoạch", "shopping list", "bữa tối"]):
            return self._tool_call("call_2", "create_food_plan", {"user_id": observation.get("user_id", "USER001"), "meal_name": "Ức gà áp chảo với cải bó xôi", "ingredients_to_use": ["sữa tươi", "cải bó xôi", "ức gà"], "missing_items": ["chanh"], "priority": "use_expiring_items_first"}, "Đã có inventory và người dùng yêu cầu tạo kế hoạch; gọi create_food_plan.")
        if last_tool == "fridge_query":
            names = ", ".join(i["name"] for i in observation.get("items", []))
            return {"type": "text", "content": f"Inventory hiện có: {names}. Món sắp hết hạn nhất là sữa tươi (2026-09-13) và cải bó xôi (2026-09-14).", "thought": "Đã có inventory; trả lời dựa trên observation."}
        if last_tool == "create_food_plan":
            plan = observation.get("plan", {})
            return {"type": "text", "content": f"Đã tạo meal plan {plan.get('plan_id')}: {plan.get('meal_name')}. Dùng: {', '.join(plan.get('ingredients_to_use', []))}. Cần mua: {', '.join(plan.get('missing_items', [])) or 'không có'}.", "thought": "Đã đủ kết quả từ tools để trả lời."}
        return {"type": "text", "content": "Tôi đã xử lý xong yêu cầu.", "thought": "Dừng an toàn."}

    def _tool_call(self, call_id: str, name: str, args: Dict[str, Any], thought: str) -> Dict[str, Any]:
        return {"type": "tool_call", "tool_call_id": call_id, "tool_name": name, "arguments": args, "thought": thought, "assistant_message": {"role": "assistant", "content": None, "tool_calls": [{"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]}}



class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
        self.base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        self.model_name = os.getenv("OPENAI_COMPATIBLE_MODEL") or "missing-model"
        self.ready = bool(self.api_key and self.base_url and not self.api_key.startswith("replace_") and not self.base_url.startswith("replace_") and not self.model_name.startswith("replace_"))
        self._mock = MockOfflineProvider()
        if not self.ready:
            print("⚠️ [OpenAI-Compatible]: thiếu cấu hình OPENAI_COMPATIBLE_*; dùng MockOfflineProvider.")

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.ready:
            return self._mock.generate(prompt, system_prompt)
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=60)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}] if system_prompt else [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(model=self.model_name, messages=messages)
        return response.choices[0].message.content or ""

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.ready:
            return self._mock.generate_with_tools(messages, tools_schema, system_prompt)
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=60)
        api_messages = [{"role": "system", "content": system_prompt}] + messages if system_prompt else messages
        tools = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""), "parameters": t.get("parameters", {})}} for t in tools_schema]
        response = client.chat.completions.create(model=self.model_name, messages=api_messages, tools=tools, tool_choice="auto")
        msg = response.choices[0].message
        if msg.tool_calls:
            call = msg.tool_calls[0]
            args = json.loads(call.function.arguments or "{}")
            return {"type": "tool_call", "tool_call_id": call.id, "tool_name": call.function.name, "arguments": args, "assistant_message": msg.model_dump(), "thought": f"LLM quyết định gọi {call.function.name}."}
        return {"type": "text", "content": msg.content or "", "assistant_message": msg.model_dump(), "thought": "LLM trả lời trực tiếp."}


def get_llm_provider() -> BaseLLMProvider:
    return MockOfflineProvider() if os.getenv("LLM_PROVIDER", "openai_compatible").lower() == "mock" else OpenAICompatibleProvider()
