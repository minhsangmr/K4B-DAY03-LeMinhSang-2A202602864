"""Reference demo for native MCP tool calling in Smart Fridge domain."""


def run_level3_demo():
    print("=== DEMO CẤP ĐỘ 3: NATIVE MCP AGENT ===")
    print("🎯 Goal: Kiểm tra inventory USER001 rồi tạo meal plan")
    print("🧠 [Thought]: Cần gọi fridge_query trước.")
    print("🛠️ [Native Tool Call]: fridge_query({'user_id': 'USER001'})")
    print("👁️ [MCP Server Observation]: {'status': 'SUCCESS', 'items': ['sữa tươi', 'cải bó xôi', 'ức gà']}")
    print("🛠️ [Native Tool Call]: create_food_plan({'user_id': 'USER001', 'priority': 'use_expiring_items_first'})")
    print("🏁 [Final Answer]: Đã tạo meal plan ưu tiên nguyên liệu sắp hết hạn.")


if __name__ == "__main__":
    run_level3_demo()

