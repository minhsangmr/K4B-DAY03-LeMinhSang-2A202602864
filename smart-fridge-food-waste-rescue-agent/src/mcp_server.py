"""Smart Fridge MCP server wrapper."""

import json
import sys
from typing import Any, Dict, List

try:
    from .tools import TOOLS_SCHEMA, dispatch_tool_call
except ImportError:
    from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MCPFridgeServer:
    """Giả lập MCP Server tuân thủ JSON-RPC 2.0 cho Smart Fridge tools."""

    def __init__(self, server_name: str = "smart-fridge-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách tools công bố qua MCP."""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Thực thi tool và bọc phản hồi theo JSON-RPC 2.0."""
        content = json.loads(dispatch_tool_call(tool_name, arguments))
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content,
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (smart-fridge-mcp-server)")
    print("==========================================================")

    server = MCPFridgeServer()
    tools = server.list_tools()
    print(f"✅ [MCP SERVER] Đã khởi tạo thành công {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố qua MCP: {len(tools)}")

    test_result = server.call_tool("fridge_query", {"user_id": "USER001"})
    print("✅ Smoke test fridge_query(USER001):")
    print(json.dumps(test_result, ensure_ascii=False, indent=2))

