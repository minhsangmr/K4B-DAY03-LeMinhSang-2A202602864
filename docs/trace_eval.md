# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** [Điền Họ và Tên]  
> **Mã Sinh Viên / Mã Học viên:** [Điền MSSV]  
> **Chủ đề Lựa chọn:** Trợ lý Tủ lạnh Thông minh chống lãng phí thực phẩm (Smart Fridge Food-Waste Rescue Agent)  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

**Mô tả ngắn:** Agent hỗ trợ người dùng tra cứu thực phẩm hiện có trong tủ lạnh, phát hiện nguyên liệu sắp hết hạn, đề xuất cách ưu tiên sử dụng và tạo kế hoạch bữa ăn, danh sách mua bổ sung hoặc lịch nhắc nhằm giảm lãng phí thực phẩm.

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5 / 5 | Inventory → hạn dùng → chọn nguyên liệu ưu tiên → xác định món → xác định nguyên liệu thiếu → hành động. |
| **2. Tool Interaction** | 5 / 5 | Cần tool đọc inventory và tool hành động tạo kế hoạch bữa ăn, danh sách mua bổ sung hoặc lịch nhắc. |
| **3. Dynamic Decision** | 5 / 5 | Tool tiếp theo phụ thuộc observation: đủ nguyên liệu thì không mua thêm; thiếu thì tạo shopping list; `NOT_FOUND` thì dừng. |
| **4. Long Horizon Goal** | 3 / 5 | Có mục tiêu xuyên suốt giảm lãng phí qua nhiều bước, nhưng lab chưa có planning/memory dài hạn nhiều phiên. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | Bài toán phù hợp triển khai Agentic System vì tổng điểm > 12/20. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE)

Kết quả sinh từ `docs/trace_waterfall.json` sau khi chạy:

```bash
python src/app.py --all
```

Tổng quan trace:

- Số test case đã chạy: 5 / 5.
- Số event trace: 11.
- Số final answers: 5.
- Số tool calls qua MCP Server: 6.
- `fridge_query`: 4 lượt.
- `create_food_plan`: 2 lượt.
- Có latency trong mọi event: Có.
- Tổng latency: 44881.77 ms.
- Latency trung bình: 4080.16 ms/event.
- Có multi-step trace 2 tool calls (`fridge_query -> create_food_plan`): Có.
- TC05 `NOT_FOUND`: Agent dừng sau `fridge_query`, không gọi `create_food_plan`, không bịa inventory.

Trích xuất trace tiêu biểu từ TC04:

```json
[
  {
    "step": 1,
    "query": "Tối nay USER001 muốn ăn món ít calo. Hãy kiểm tra tủ lạnh, ưu tiên thực phẩm sắp hết hạn, rồi tạo meal plan và shopping list cho những nguyên liệu còn thiếu.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "fridge_query",
    "arguments": {
      "user_id": "USER001"
    },
    "observation": {
      "status": "SUCCESS",
      "user_id": "USER001",
      "items": [
        {"name": "ức gà", "quantity": 300, "unit": "g", "expiry_date": "2026-09-15", "category": "protein"},
        {"name": "cải bó xôi", "quantity": 1, "unit": "bó", "expiry_date": "2026-09-14", "category": "vegetable"},
        {"name": "sữa tươi", "quantity": 500, "unit": "ml", "expiry_date": "2026-09-13", "category": "dairy"},
        {"name": "trứng", "quantity": 4, "unit": "quả", "expiry_date": "2026-09-20", "category": "protein"}
      ]
    },
    "latency_ms": 3003.04
  },
  {
    "step": 2,
    "query": "Tối nay USER001 muốn ăn món ít calo. Hãy kiểm tra tủ lạnh, ưu tiên thực phẩm sắp hết hạn, rồi tạo meal plan và shopping list cho những nguyên liệu còn thiếu.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "create_food_plan",
    "arguments": {
      "user_id": "USER001",
      "meal_name": "Ức gà áp chảo với salad cải bó xôi ít calo",
      "ingredients_to_use": ["ức gà 300g", "cải bó xôi 1 bó"],
      "missing_items": ["chanh", "tỏi", "dưa leo", "cà chua bi"],
      "reminder_time": "",
      "priority": "use_expiring_items_first"
    },
    "observation": {
      "status": "SUCCESS",
      "plan": {
        "plan_id": "PLAN-USER001-0002",
        "user_id": "USER001",
        "meal_name": "Ức gà áp chảo với salad cải bó xôi ít calo",
        "ingredients_to_use": ["ức gà 300g", "cải bó xôi 1 bó"],
        "missing_items": ["chanh", "tỏi", "dưa leo", "cà chua bi"],
        "priority": "use_expiring_items_first",
        "reminder_time": ""
      }
    },
    "latency_ms": 5335.25
  },
  {
    "step": 3,
    "query": "Tối nay USER001 muốn ăn món ít calo. Hãy kiểm tra tủ lạnh, ưu tiên thực phẩm sắp hết hạn, rồi tạo meal plan và shopping list cho những nguyên liệu còn thiếu.",
    "action_type": "FINAL_ANSWER",
    "thought": "LLM trả lời trực tiếp.",
    "output": "Meal plan đã tạo: `PLAN-USER001-0002`\n\nMón tối ít calo: Ức gà áp chảo với salad cải bó xôi.\n\nƯu tiên dùng:\n- Cải bó xôi 1 bó, hết hạn 2026-09-14\n- Ức gà 300g, hết hạn 2026-09-15\n\nKhông dùng sữa tươi dù hết hạn gần hơn 2026-09-13, vì không hợp món ít calo này.\n\nShopping list cần mua:\n- chanh\n- tỏi\n- dưa leo\n- cà chua bi",
    "latency_ms": 4591.69
  }
]
```

Ghi chú nghiệm thu live API: `docs/trace_waterfall.json` hiện là trace từ `python src/app.py --all` với OpenAI-compatible provider thật.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền đầy đủ `OPENAI_COMPATIBLE_API_KEY`, `OPENAI_COMPATIBLE_BASE_URL`, `OPENAI_COMPATIBLE_MODEL` trong `.env` và xác nhận Agent chạy mượt trên OpenAI-compatible API thật.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 6 lượt.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
