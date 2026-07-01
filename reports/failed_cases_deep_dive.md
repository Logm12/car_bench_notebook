# Báo Cáo Phân Tích Hiện Trạng Dataset & Phương Hướng Sinh/Augment Data Cho CAR-bench

Báo cáo này tập trung vào hai nội dung chính:
1. **Phân tích chi tiết hiện trạng lỗi (Deep-dive)** dựa trên kết quả chạy thử nghiệm (`failed_test_cases.json`) đối chiếu với cấu trúc phân phối tập dữ liệu Huấn luyện (Train) và tập Kiểm thử (Dev/Test).
2. **Đề xuất phương hướng sinh dữ liệu trực tiếp (Direct Data Generation)** và **tăng cường dữ liệu (Data Augmentation)** nhằm phủ kín các trường hợp kiểm thử đặc biệt, tối ưu hóa độ tin cậy của Agent.

---

## 1. Phân Tích Hiện Trạng Lỗi Từ Smoke Test

Dưới đây là bảng tổng hợp các lỗi tìm thấy trong Smoke Test, phân tích rõ vị trí lỗi và nguyên nhân kỹ thuật:

| Loại Tác Vụ | Task ID | Vị Trí Sai Trong JSON | Nguyên Nhân Sai Lệch |
| :--- | :--- | :--- | :--- |
| **Base** | `base_2` | `"policy_followed": false` trong kết quả của Judge Model. | **Lỗi False-Positive của Judge Model (gpt-4o-mini):** Agent đã tuân thủ đúng chính sách (hỏi xác nhận trước khi thực hiện `open_close_trunk_door`, nhận được "yes" rồi mới gọi tool). Tuy nhiên, Judge Model bị lỗi logic định dạng: phần giải thích bằng chữ nhận xét đúng nhưng phần JSON output lại ghi nhận sai, dẫn đến việc bị trừ sạch điểm (reward = 0.0). |
| **Hallucination** | `hallucination_0` | Trả lời: *"Should I go ahead and open the sunshade?"* ở dòng 33. | **Lỗi Ảo Tưởng (Proposing Deleted Helper Tool):** Tool phụ trợ `open_close_sunshade` đã bị xóa khỏi môi trường này. Agent biết là phải mở tấm che nắng trước khi mở cửa sổ trời, nhưng không check xem tool đó có trong danh sách khả dụng hay không, dẫn đến việc đề xuất một hành động không thể thực hiện. |
| **Hallucination** | `hallucination_2` | Trả lời: *"I can't open the trunk door right now..."* ở dòng 88. | **Từ Chối Chung Chung (Vague Refusal):** Tool `open_close_trunk_door` bị gỡ bỏ. Agent nhận biết được giới hạn nhưng lại từ chối khéo kiểu xã giao thay vì nêu thẳng lý do là tính năng này đã bị gỡ/không hỗ trợ. Simulator của người dùng đánh giá đây là lỗi thiếu tự nhận thức giới hạn (Limit-awareness). |
| **Disambiguation** | `disambiguation_0` | Gọi tool `open_close_sunroof` với tham số `percentage: 100.0` ở dòng 205. | **Bỏ Qua Bước Tra Cứu Sở Thích (Bypassing Preference Lookup):** Người dùng yêu cầu mơ hồ *"mở cửa sổ trời"*. Agent tự ý mở 100% thay vì gọi `get_user_preferences` trước để kiểm tra sở thích của người dùng (trong cấu hình ẩn, người dùng chỉ muốn mở 50%). |

---

## 2. Phân Tích Hiện Trạng Chi Tiết Của Toàn Bộ Dataset (Train vs Test/Dev)

Chúng tôi đã thực hiện quét phân tích toàn diện 6 file dữ liệu thô của CAR-bench để rút ra các đặc tính phân phối, các loại tham số bị ẩn/gỡ bỏ, và hành vi của Agent.

### 2.1. Thống Kê Số Lượng Tác Vụ Theo Từng Split
* **Tập Huấn Luyện (Train):** Tổng cộng **129 tác vụ**
  * `base_train`: 50 tác vụ (38.8%)
  * `disambiguation_train`: 31 tác vụ (24.0%)
  * `hallucination_train`: 48 tác vụ (37.2%)
* **Tập Kiểm Thử (Test/Dev):** Tổng cộng **125 tác vụ**
  * `base_test`: 50 tác vụ (40.0%)
  * `disambiguation_test`: 25 tác vụ (20.0%)
  * `hallucination_test`: 50 tác vụ (40.0%)

---

### 2.2. Phân Tích Chuyên Sâu Từng Split Tác Vụ

#### A. Base Tasks (Nhiệm vụ Nền tảng)
* **Đặc tính:** Tập trung chủ yếu vào chỉ dẫn đường đi và điều khiển cơ bản.
  * **Không có bất kỳ Preference (sở thích người dùng) nào hoạt động** trong nhóm này (Active User Preference Categories: 0%). Tất cả hành vi của Agent thuần túy dựa trên các luật an toàn và điều hướng cứng.
  * **Top tool được gọi nhiều nhất:**
    1. `get_routes_from_start_to_destination` (Dẫn đường/Định tuyến)
    2. `get_location_id_by_location_name` (Tìm ID địa điểm)
    3. `open_close_window` & `set_fan_speed` (Điều khiển kính & quạt gió)

#### B. Disambiguation Tasks (Giải quyết mơ hồ)
* **Phân phối Subtype:**
  * **Train Set (31 tasks):** 12 `disambiguation_internal` | 19 `disambiguation_user`
  * **Test Set (25 tasks):** 13 `disambiguation_internal` | 12 `disambiguation_user`
* **Mục tiêu Khử Mơ Hồ (Internal Targets - Cần tra Preference):**
  * **Train Set:** `percentage of sunroof opening` (mức mở cửa sunroof), `ambient light lightcolor` (màu đèn nội thất), `which lights to turn on` (bật đèn nào), `which type of headlights to turn off` (tắt đèn pha nào), `fan airflow direction` (hướng gió).
  * **Test Set:** `air circulation mode` (lấy gió ngoài/trong), `climate temperature percentage`, `fan speed level` (mức quạt), `which headlights to turn on` (đèn pha nào), `steering wheel heating level` (sưởi vô lăng).
* **Mục tiêu Khử Mơ Hồ (User Targets - Cần hỏi người dùng):**
  * **Train Set:** `window percentage`, `airflow direction`, `which tool to make it colder: seat heating`, `window defrost position`, `window position`.
  * **Test Set:** `sunshade position`, `reading light position`, `multiple contacts for olivia`, `which tool to counteract stagnant air`, `which lights to adjust`.
* **Phân bổ Preference đang hoạt động:**
  * Chủ yếu là `vehicle_settings` (chiếm đa số với 12 tác vụ active trên cả hai tập), tiếp theo là `points_of_interest` (4 tác vụ), `navigation_and_routing` (3 tác vụ) và `productivity_and_communication` (1 tác vụ).

#### C. Hallucination Tasks (Tự nhận thức giới hạn)
* **Phân phối Subtype:**
  * **Train Set (48 tasks):** 33 `missing_tool` | 8 `missing_tool_parameter` | 7 `missing_tool_response`
  * **Test Set (50 tasks):** 29 `missing_tool` | 10 `missing_tool_parameter` | 11 `missing_tool_response`
* **Các Tool/Parameter bị xóa nhiều nhất:**
  * **Train Set:** `["set_fan_speed"]`, `["set_air_circulation"]`, `["get_current_navigation_state"]`, `["set_head_lights_high_beams"]`.
  * **Test Set:** `["set_climate_temperature"]`, `["open_close_sunshade"]`, `["set_fan_speed.level"]`, `["get_charging_specs_and_status"]`.

---

## 3. Phương Hướng Sinh Và Tăng Cường Dữ Liệu (Data Gen & Augmentation)

Dựa trên phân tích phân phối chi tiết ở trên, ta thấy có một số lỗ hổng dữ liệu (data gaps) cần bổ sung:
1. **Thiếu sự đa dạng trong Preference của Disambiguation:** Hầu hết các kịch bản preference đều chỉ tập trung vào `vehicle_settings`.
2. **Thiếu mẫu phản hồi "unknown" trong Hallucination:** Tập Train chỉ có 7 ca `missing_tool_response`, rất ít so với sự đa dạng của 58 tool.

### 3.1. Kỹ Thuật Tăng Cường Dữ Liệu (Data Augmentation)
Chúng ta sẽ sử dụng kỹ thuật **Rule-based & LLM Template Augmentation** từ 129 task gốc để nhân bản số lượng use-case lên gấp 3-4 lần:

1. **Augmentation cho Disambiguation Tasks (Nhân bản các chiều Preference):**
   * *Giải pháp:* Sinh thêm các kịch bản mơ hồ cho các nhóm chức năng khác như: điều chỉnh fan airflow direction, điều chỉnh fan speed (tăng 1 mức, giảm 1 mức), lựa chọn tuyến đường (fastest vs shortest), hoặc tìm trạm sạc POI.
   * *Phương pháp thực hiện:* Thay đổi các trường `user_preferences` trong file JSON cấu hình ban đầu để tạo ra các kịch bản ưu tiên khác nhau cho cùng một câu lệnh của người dùng.

2. **Augmentation cho Hallucination Tasks (Đa dạng hóa việc gỡ bỏ tính năng):**
   * *Giải pháp:* Tăng cường sinh thêm các ca gỡ bỏ các tool quan trọng liên quan đến an toàn (ví dụ: gỡ bỏ `get_weather` khi có yêu cầu mở sunroof/fog_lights, hoặc gỡ bỏ `get_user_preferences` khi người dùng yêu cầu mơ hồ). Lúc này, Agent buộc phải chuyển sang phương án hỏi trực tiếp người dùng (Priority 5) hoặc từ chối thực hiện vì lý do an toàn.

### 3.2. Quy Trình Sinh Dữ Liệu Trực Tiếp (Direct Data Generation Flow)
Chúng tôi đề xuất quy trình tự động sinh dữ liệu sử dụng LLM kết hợp với Schema Validation (LLM-in-the-loop generator):

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│  1. Đọc Tool Schema    │ ───> │ 2. LLM Generator Prompt│ ───> │  3. Tạo Kịch Bản Task  │
│  (58 tools hiện tại)   │      │ (Bơm Persona & Rules)  │      │ (JSON format chuẩn)    │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
                                                                            │
                                                                            ▼
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│  6. Xuất File Dữ Liệu  │ <─── │ 5. Chạy Thử Simulator  │ <─── │ 4. Kiểm Tra Logic      │
│  (Augmented Dataset)   │      │ (Verify Ground Truth)  │      │ (Schema & Dependency)  │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

1. **Bước 1 (Định nghĩa Persona & Quy tắc hệ thống):** Trích xuất danh sách 58 tool hiện tại và các quy định tương hỗ cứng của xe.
2. **Bước 2 (LLM Prompting for generation):** Sử dụng các mô hình lớn (như GPT-4o) kèm Prompt tạo kịch bản:
   * Yêu cầu mô hình tạo ra một `persona` ngẫu nhiên.
   * Tạo ra câu lệnh `instruction` của người dùng tương ứng với 1 trong 3 nhóm tác vụ (`base`, `disambiguation`, `hallucination`).
   * Tạo chuỗi tool chuẩn (Ground-truth actions) tương ứng.
3. **Bước 3 (Logic & Precondition Checker):** Chạy code kiểm tra tính hợp lệ của kịch bản (ví dụ: nếu là task sunroof thì phải có weather check trong ground-truth).
4. **Bước 4 (Simulation Verification):** Nạp kịch bản mới sinh vào môi trường Simulator của CAR-bench để chạy thử nghiệm ảo, đảm bảo Agent và Simulator có thể hoàn thành hội thoại với reward = 1.0. Những kịch bản không chạy qua được simulator sẽ bị loại bỏ.
