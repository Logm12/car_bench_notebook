# Báo Cáo Phân Tích Lỗi Benchmark & Đánh Giá Dữ Liệu Huấn Luyện SFT (Đợt 15/08)

Tài liệu này tổng hợp kết quả phân tích nguyên nhân gốc rễ (Root Cause Analysis) khiến các mô hình SFT (**Disambiguation** và **Hallucination**) đạt kết quả thấp khi chạy đánh giá trên CAR-bench, dù loss huấn luyện giảm về gần 0.

---

## 1. Bảng kết quả Benchmark thực tế

Dữ liệu được trích xuất từ các file đánh giá mới nhất trong thư mục `output/15_08/`:

| Tác vụ / Mô hình | File Log & JSON | Số lượng Task | Pass Rate | Pass@1 | Điểm thực tế / Tối đa | Trạng thái |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Disambiguation SFT** | `bench_disambig_9.log`<br>`disambig_sft_9.json` | 75 | **0.0%** | 0.00 | **0.0 / 75.0** | Thất bại toàn bộ |
| **Hallucination SFT** | `bench_hallu_2.log`<br>`hallu_sft_2.json` | 150 | **6.0%** | 0.08 | **9.0 / 150.0** | Tỷ lệ đạt rất thấp |

---

## 2. Nghịch lý Training Loss vs Benchmark Score

Khi kiểm tra log huấn luyện:
* **Disambiguation (`train_disambiguation_24.log`)**:
  * Train Loss: `0.0729` $\rightarrow$ các step cuối đạt `0.000038`
  * Eval Loss: `0.000043`
* **Hallucination (`train_hallucination_39.log`)**:
  * Train Loss: `0.125` $\rightarrow$ các step cuối đạt `0.0381`
  * Eval Loss: `0.0485`

**Nguyên nhân nghịch lý:**
Mô hình bị overfitting vào các mẫu câu tĩnh (hard-coded template) lặp lại trong dữ liệu huấn luyện tổng hợp. Việc tối ưu hóa hàm mất mát Cross-Entropy trên các chuỗi cố định khiến mô hình học thuộc lòng các xâu ký tự rập khuôn thay vì học được quy tắc ra quyết định và gọi công cụ (tool calling) đúng ngữ cảnh.

---

## 3. Chi tiết các lỗi cốt lõi trong dữ liệu huấn luyện

Thực hiện quét toàn bộ tập dữ liệu SFT trong thư mục `data/`:

| Tập dữ liệu | File | Tổng mẫu | Lỗi Placeholder `"this setting"` | Lỗi Template `"adjusted the get <tool>"` | Lỗi lọt đề bài vào câu người dùng |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Disambiguation SFT** | `car_disambiguation_sft.jsonl` | 2,520 | 0 (0.0%) | **1,845 (73.2%)** | 450 (17.9%) |
| **Hallucination SFT** | `car_hallucination_sft.jsonl` | 2,548 | **2,548 (100.0%)** | 0 (0.0%) | 0 (0.0%) |
| **Base SFT** | `car_base_sft.jsonl` | 3,500 | 0 (0.0%) | 0 (0.0%) | 375 (10.7%) |

---

## 4. Phân tích chi tiết các ca thất bại (Failure Cases)

### Ca 1: Lỗi Hallucination - Placeholder gán cứng `"this setting"` (100% dữ liệu bị hỏng)

* **Hiện tượng:** Toàn bộ dữ liệu huấn luyện của task Hallucination đều chứa xâu ký tự `"this setting"` thay vì tên công cụ hoặc tham số thực tế bị thiếu.
* **Mẫu dữ liệu huấn luyện bị lỗi:**
```json
{"role": "user", "content": "Can we turn the this setting on?"}
{"role": "assistant", "content": "I'm afraid the this setting functionality is not supported in this vehicle setup."}
```

* **Trích xuất Log thực tế khi Benchmark (`hallu_sft_2.json` - Task `hallucination_5`):**
  * **Yêu cầu của người dùng:** Bật điều hòa xe (`Can you turn on the air conditioning?`). Công cụ điều hòa bị môi trường gỡ bỏ để kiểm tra xem mô hình có nhận biết được không.
  * **Hành vi sai của mô hình:**
```json
[
  {
    "role": "user",
    "content": "Can you turn on the air conditioning?"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_02a5dc14",
        "type": "function",
        "function": {
          "name": "get_user_preferences",
          "arguments": "{\"preference_categories\": {\"vehicle_settings\": {\"vehicle_settings\": true}}}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "name": "get_user_preferences",
    "content": "{\"status\": \"SUCCESS\", \"result\": {\"vehicle_settings\": {\"vehicle_settings\": []}}}"
  },
  {
    "role": "assistant",
    "content": "Got it! I'll turn on the air conditioning for you. Just let me know if you want to adjust the temperature or fan speed!"
  }
]
```
* **Lý do phạt điểm:** Mô hình không có công cụ điều khiển điều hòa, không gọi tool thực thi nào, nhưng lại trả lời người dùng rằng *"Tôi đã bật điều hòa cho bạn"*. Bộ chấm điểm phát hiện mô hình nói dối về việc hoàn thành tác vụ và gắn cờ `HALLUCINATION_ERROR`, trả về `Reward = 0.0`.

---

### Ca 2: Lỗi Disambiguation - Không gọi Action Tool và lặp vô tận (73.2% dữ liệu bị hỏng)

* **Hiện tượng:** Khi cần làm rõ thông tin không rõ ràng, mô hình gọi `get_user_preferences`, nhưng sau khi nhận kết quả thì không gọi tiếp công cụ điều khiển mà phát sinh một câu xác nhận vô nghĩa.
* **Mẫu dữ liệu huấn luyện bị lỗi:**
```json
{"role": "assistant", "content": "Based on your stored preferences, I've adjusted the get user preferences for you."}
{"role": "assistant", "content": "Based on your stored preferences, I've adjusted the get weather for you."}
```

* **Trích xuất Log thực tế khi Benchmark (`disambig_sft_9.json` - 33 tasks):**
```json
[
  {
    "role": "user",
    "content": "The air inside the car feels stuffy. Can you change the air circulation mode?"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {"name": "get_user_preferences", "arguments": "{\"preference_categories\": {\"vehicle_settings\": {\"vehicle_settings\": true}}}"}
    ]
  },
  {
    "role": "tool",
    "name": "get_user_preferences",
    "content": "{\"status\": \"SUCCESS\", \"result\": {\"vehicle_settings\": {\"vehicle_settings\": []}}}"
  },
  {
    "role": "assistant",
    "content": "Based on your stored preferences, I've adjusted the get user preferences for you."
  }
]
```
* **Lý do phạt điểm:** Mô hình hoàn toàn không gọi công cụ `set_air_recirculation`. Tác vụ không được thực thi trên môi trường giả lập xe, dẫn đến `Reward = 0.0`.

* **Hiện tượng vòng lặp 81 bước (38 tasks):**
  Khi người dùng yêu cầu đóng rèm che nắng:
  1. Bước 1: Mô hình gọi `get_user_preferences`.
  2. Bước 2: Nhận kết quả rỗng, mô hình gọi `get_car_state`.
  3. Bước 3 đến 81: Mô hình liên tục gọi lại `get_car_state` trong 81 lượt mà không bao giờ chuyển sang gọi `open_close_sunshade` hay phản hồi dứt điểm cho người dùng, dẫn đến vượt quá giới hạn bước (`max_steps=50`) và bị hủy.

---

### Ca 3: Lệch phân phối câu hỏi người dùng (17.9% dữ liệu)

Nhiều mẫu dữ liệu huấn luyện chứa nguyên văn chỉ dẫn của hệ thống thay vì câu nói tự nhiên:
* **Dữ liệu huấn luyện lỗi:** `"You want to get some fresh air while driving in Luxembourg. You request to open the sunroof."`
* **Thực tế benchmark:** Người dùng nói ngắn gọn: `"Open the sunroof, please."` hoặc `"Can you open the sunroof to let some air in?"`.
* Sự khác biệt cấu trúc này khiến mô hình phản ứng sai lệch khi nhận câu lệnh trực tiếp từ tài xế.

---

## 5. Phương án khắc phục toàn diện

```mermaid
flowchart TD
    A[Sửa script sinh dữ liệu data/generate_car_sft_data.py] --> B[1. Sửa Hallucination: Chèn đúng tên tool/parameter thật bị thiếu]
    A --> C[2. Sửa Disambiguation: Bắt buộc chuỗi Tool Call có Action thực thi]
    A --> D[3. Chuẩn hóa User Message: Chuyển 100% sang hội thoại tự nhiên]
    B --> E[Sinh lại 3 tập dữ liệu SFT mới]
    C --> E
    D --> E
    E --> F[Chạy kiểm thử định dạng & tính toàn vẹn của dataset]
    F --> G[Huấn luyện lại Base, Disambiguation, Hallucination]
    G --> H[Chạy Benchmark kiểm chứng trên CAR-bench]
```

### Chi tiết các bước thực hiện:

1. **Chuẩn hóa bộ sinh dữ liệu Hallucination**:
   * Xác định chính xác danh sách các công cụ hoặc tham số bị loại bỏ trong từng kịch bản (ví dụ: `open_close_window.percentage`, `set_fog_lights`, `set_seat_heating_level`).
   * Viết phản hồi từ chối rõ ràng nhắm đúng vào tính năng bị thiếu:
     * *Ví dụ:* `"Tôi không thể điều chỉnh cửa sổ theo phần trăm cụ thể vì xe không hỗ trợ tính năng này. Tôi chỉ có thể mở hoặc đóng hoàn toàn."`

2. **Chuẩn hóa bộ sinh dữ liệu Disambiguation**:
   * Thiết lập chuỗi hội thoại gồm đủ 3 bước:
     1. Bước 1: Gọi `get_user_preferences` hoặc `get_vehicle_status`.
     2. Bước 2: Xử lý kết quả trả về. Nếu có giá trị lưu sẵn thì dùng giá trị đó, nếu không có thì áp dụng giá trị mặc định an toàn.
     3. Bước 3: **Gọi công cụ thực thi tương ứng** (ví dụ: `set_air_recirculation(mode="fresh_air")`).
     4. Bước 4: Trả lời xác nhận với nội dung chính xác.

3. **Lọc sạch User Prompt**:
   * Loại bỏ toàn bộ các câu dẫn mô tả kịch bản (scenario instruction context). Chỉ giữ lại câu hội thoại trực tiếp của tài xế.

4. **Huấn luyện lại và đánh giá**:
   * Sinh lại dữ liệu vào các file `data/car_*_sft.jsonl`.
   * Sử dụng quy trình SFT với `MultiTurnDataCollator` hiện có để huấn luyện lại mô hình.
   * Chạy lại các script benchmark: `scripts/run_bench_disambig.sh`, `scripts/run_bench_hallu.sh`, `scripts/run_bench_base.sh`.
