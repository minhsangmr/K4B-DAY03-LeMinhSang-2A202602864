# Smart Fridge Food-Waste Rescue Agent

Trợ lý tủ lạnh thông minh chống lãng phí thực phẩm. Agent dùng ReAct loop, MCP-style server, tool calling và Waterfall Trace để tra cứu inventory, ưu tiên nguyên liệu sắp hết hạn, tạo meal plan và shopping list.

## Kiến trúc

```text
User / CLI
  -> ReAct Agent (src/app.py)
  -> OpenAI-compatible Provider (src/providers.py)
  -> MCPFridgeServer (src/mcp_server.py)
  -> Tools (src/tools.py)
       - fridge_query
       - create_food_plan
```

## Nguyên tắc chống hallucination

- Không tự bịa inventory.
- Muốn biết tủ lạnh có gì thì gọi `fridge_query`.
- Chỉ gọi `create_food_plan` sau khi có inventory hợp lệ.
- Nếu `fridge_query` trả `NOT_FOUND`, dừng và báo rõ; không tạo kế hoạch từ dữ liệu tưởng tượng.

## Tools

### `fridge_query`

Tra cứu inventory theo `user_id`.

```json
{"user_id": "USER001"}
```

### `create_food_plan`

Tạo meal plan, danh sách nguyên liệu dùng, món cần mua thêm, priority/reminder.

```json
{
  "user_id": "USER001",
  "meal_name": "Ức gà áp chảo với cải bó xôi",
  "ingredients_to_use": ["sữa tươi", "cải bó xôi", "ức gà"],
  "missing_items": ["chanh"],
  "priority": "use_expiring_items_first"
}
```

## Setup bằng `uv`

```bash
cd smart-fridge-food-waste-rescue-agent
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

Hoặc dùng `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Cấu hình provider

`.env.example`:

```env
LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=replace_with_your_9router_api_key
OPENAI_COMPATIBLE_BASE_URL=replace_with_your_9router_openai_compatible_base_url
OPENAI_COMPATIBLE_MODEL=replace_with_model_id_available_on_9router
```

Mock offline:

```bash
LLM_PROVIDER=mock python src/app.py --all
```

API thật:

```bash
python src/app.py --all
```

Yêu cầu `.env` có đủ `OPENAI_COMPATIBLE_API_KEY`, `OPENAI_COMPATIBLE_BASE_URL`, `OPENAI_COMPATIBLE_MODEL`. Không commit `.env`.

## Chạy CLI

Chạy 5 test cases:

```bash
python src/app.py --all
```

Interactive chat:

```bash
python src/app.py --interactive
```

Smoke test MCP server:

```bash
python src/mcp_server.py
```

## Artifacts nộp bài

- `config/test_cases.json`: 5 test cases Smart Fridge.
- `docs/trace_waterfall.json`: Waterfall Trace sinh từ test suite.
- `docs/trace_eval.md`: báo cáo Agentic Fit + trace summary.
- `src/`: source code Agent, provider, MCP server, tools, prompts.

## Kết quả nghiệm thu hiện tại

- 5/5 test cases chạy xong.
- 11 trace events.
- 6 MCP tool calls.
- TC04 có multi-step `fridge_query -> create_food_plan -> final answer`.
- TC05 `NOT_FOUND` không gọi `create_food_plan`, không bịa inventory.

## Lưu ý mock vs live API

`OpenAICompatibleProvider` là provider mặc định. Nếu thiếu cấu hình thật hoặc còn placeholder, provider cảnh báo và fallback sang `MockOfflineProvider` để lab vẫn chạy offline. Khi nộp nghiệm thu live, điền `.env` thật rồi chạy lại `python src/app.py --all` để cập nhật trace.
