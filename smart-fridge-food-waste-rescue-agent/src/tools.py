"""Smart Fridge tool schemas and execution backend."""

import json
from typing import Any, Dict, List, Optional

TOOLS_SCHEMA = [
    {
        "name": "fridge_query",
        "description": "Tra cứu inventory hiện có trong tủ lạnh của người dùng, gồm số lượng, đơn vị, nhóm thực phẩm và hạn sử dụng.",
        "parameters": {"type": "object", "properties": {"user_id": {"type": "string", "description": "Mã người dùng/chủ tủ lạnh, ví dụ USER001"}}, "required": ["user_id"], "additionalProperties": False},
    },
    {
        "name": "create_food_plan",
        "description": "Tạo kế hoạch bữa ăn dựa trên inventory đã tra cứu, lưu danh sách nguyên liệu sử dụng, nguyên liệu cần mua thêm và thời gian nhắc nếu có.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "meal_name": {"type": "string"},
                "ingredients_to_use": {"type": "array", "items": {"type": "string"}},
                "missing_items": {"type": "array", "items": {"type": "string"}},
                "reminder_time": {"type": "string", "description": "Thời gian nhắc dạng chuỗi ISO-8601; bỏ trống nếu không cần"},
                "priority": {"type": "string", "enum": ["use_expiring_items_first", "normal"]},
            },
            "required": ["user_id", "meal_name", "ingredients_to_use", "missing_items", "priority"],
            "additionalProperties": False,
        },
    },
]

FRIDGE_DB: Dict[str, List[Dict[str, Any]]] = {
    "USER001": [
        {"name": "ức gà", "quantity": 300, "unit": "g", "expiry_date": "2026-09-15", "category": "protein"},
        {"name": "cải bó xôi", "quantity": 1, "unit": "bó", "expiry_date": "2026-09-14", "category": "vegetable"},
        {"name": "sữa tươi", "quantity": 500, "unit": "ml", "expiry_date": "2026-09-13", "category": "dairy"},
        {"name": "trứng", "quantity": 4, "unit": "quả", "expiry_date": "2026-09-20", "category": "protein"},
    ]
}

FOOD_PLANS_DB: List[Dict[str, Any]] = []


def execute_fridge_query(user_id: str) -> str:
    user_id = user_id.strip().upper()
    items = FRIDGE_DB.get(user_id)
    if items is None:
        return json.dumps({"status": "NOT_FOUND", "message": f"Không tìm thấy inventory cho user_id '{user_id}'"}, ensure_ascii=False)
    return json.dumps({"status": "SUCCESS", "user_id": user_id, "items": items}, ensure_ascii=False)


def execute_create_food_plan(user_id: str, meal_name: str, ingredients_to_use: List[str], missing_items: List[str], priority: str, reminder_time: Optional[str] = None) -> str:
    if not user_id or not meal_name:
        return json.dumps({"status": "ERROR", "message": "user_id và meal_name là bắt buộc."}, ensure_ascii=False)
    if not isinstance(ingredients_to_use, list) or not isinstance(missing_items, list):
        return json.dumps({"status": "ERROR", "message": "ingredients_to_use và missing_items phải là list."}, ensure_ascii=False)
    if priority not in {"use_expiring_items_first", "normal"}:
        return json.dumps({"status": "ERROR", "message": "priority không hợp lệ."}, ensure_ascii=False)
    user_id = user_id.strip().upper()
    plan = {"plan_id": f"PLAN-{user_id}-{len(FOOD_PLANS_DB) + 1:04d}", "user_id": user_id, "meal_name": meal_name, "ingredients_to_use": ingredients_to_use, "missing_items": missing_items, "priority": priority, "reminder_time": reminder_time}
    FOOD_PLANS_DB.append(plan)
    return json.dumps({"status": "SUCCESS", "plan": plan}, ensure_ascii=False)


TOOL_ROUTER = {"fridge_query": execute_fridge_query, "create_food_plan": execute_create_food_plan}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    if not isinstance(arguments, dict):
        return json.dumps({"status": "ERROR", "message": "arguments phải là dict."}, ensure_ascii=False)
    handler = TOOL_ROUTER.get(tool_name)
    if handler is None:
        return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
    try:
        return handler(**arguments)
    except Exception as exc:
        return json.dumps({"status": "EXECUTION_ERROR", "error": str(exc)}, ensure_ascii=False)

