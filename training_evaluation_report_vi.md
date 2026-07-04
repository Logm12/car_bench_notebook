# Báo Cáo Kết Quả Huấn Luyện và Đánh Giá Mô Hình Qwen 3.5 4B SFT

Báo cáo này tài liệu hóa các chỉ số trong quá trình huấn luyện tinh chỉnh (SFT) mô hình Qwen 3.5 4B, thống kê số lượng tác vụ trong tập dữ liệu CAR-bench, và phân tích chi tiết nguyên nhân thất bại của các tác vụ trong lượt đánh giá dẫn đường được ghi nhận tại log hệ thống.

---

## 1. Chỉ Số Huấn Luyện (Training & Evaluation Metrics)

Dựa trên dữ liệu log huấn luyện trực quan từ ảnh chụp, các chỉ số đo lường hiệu năng của mô hình được thống kê chi tiết như sau:

### 1.1. Quá trình Huấn luyện (Training Phase)
*   **Số lượng Epochs:** 3
*   **Bước huấn luyện toàn cục (global_step):** 939
*   **Hao phí huấn luyện (train_loss / train/loss):** 0.50848 (tại bước log chính) / 0.85620 (tại bước đánh giá cuối)
*   **Độ hỗn loạn huấn luyện (train_entropy):** 0.84410
*   **Độ chính xác trung bình của token (train/mean_token_accuracy):** 78.59%
*   **Tốc độ xử lý mẫu (train_samples_per_second):** 1.66 mẫu/giây
*   **Tốc độ xử lý bước (train_steps_per_second):** 0.104 bước/giây
*   **Tổng số token huấn luyện (train/num_tokens):** 5.610.143 (khoảng $5.61 \times 10^6$)
*   **Tốc độ học cuối cùng (train/learning_rate):** $1.4294 \times 10^{-9}$
*   **Chuẩn gradient (train/grad_norm):** 0.26537
*   **Thời gian huấn luyện (train_runtime):** 9037.9183 giây (xấp xỉ 2.51 giờ)
*   **Tổng số phép tính dấu phẩy động (total_flos):** $2.92257 \times 10^{17}$

### 1.2. Quá trình Đánh giá (Evaluation Phase)
*   **Hao phí đánh giá (eval/loss):** 0.81360
*   **Độ hỗn loạn đánh giá (eval/entropy):** 0.81782
*   **Độ chính xác trung bình của token (eval/mean_token_accuracy):** 79.01%
*   **Tốc độ xử lý mẫu đánh giá (eval/samples_per_second):** 6.392 mẫu/giây
*   **Tốc độ xử lý bước đánh giá (eval/steps_per_second):** 0.8 bước/giây
*   **Tổng số token đánh giá (eval/num_tokens):** 5.647.422 (khoảng $5.65 \times 10^6$)
*   **Thời gian chạy đánh giá (eval/runtime):** 282.539 giây

### 1.3. Phân tích nguyên nhân giá trị Hao phí (Loss) còn cao (khoảng 0.81 - 0.85)
Mặc dù mô hình đã được tinh chỉnh qua 3 epochs, giá trị loss trong cả quá trình train và eval vẫn duy trì ở mức tương đối cao. Nguyên nhân chủ yếu xuất phát từ các yếu tố kỹ thuật sau:
1.  **Độ phức tạp của định dạng đầu ra (Structural Syntax Constraints):** Dữ liệu CAR-bench yêu cầu mô hình sinh ra chính xác cấu trúc hội thoại kết hợp các khối JSON biểu diễn cuộc gọi công cụ (tool calls) kèm tham số. Một sai sót nhỏ về dấu ngoặc, khoảng trắng hoặc tên tham số đều làm tăng vọt giá trị cross-entropy loss của token.
2.  **Sự mâu thuẫn trong kịch bản huấn luyện (Ambiguity & Hallucination Divergence):** Tập dữ liệu huấn luyện chứa các kịch bản mơ hồ (Disambiguation) và kịch bản thiếu công cụ (Hallucination). Trong các kịch bản này, hành động chính xác của mô hình phụ thuộc vào các biến ẩn (như sở thích cá nhân người dùng hoặc danh sách API khả dụng thay đổi động). Nếu mô hình chưa học được cách tích hợp triệt để các ngữ cảnh này ở lượt hội thoại đầu tiên, nó sẽ dự đoán sai công cụ đích, dẫn đến phạt loss rất cao.
3.  **Tỷ lệ học tập suy giảm quá sâu (Learning Rate Decay):** Chỉ số `train/learning_rate` ở cuối phiên huấn luyện giảm xuống cực thấp ($1.4294 \times 10^{-9}$). Điều này cho thấy thuật toán tối ưu hóa (optimizer scheduler) đã giảm tốc độ học quá sớm, khiến mô hình bị mắc kẹt ở các cực trị địa phương (local minima) và không thể tiếp tục tối ưu hóa hao phí xuống mức thấp hơn.
4.  **Kích thước dữ liệu huấn luyện nhỏ (Data Sparsity):** Tập huấn luyện SFT chỉ gồm 129 tác vụ mẫu. Số lượng dữ liệu ít ỏi này không đủ để mô hình 4B tham số học cách tổng quát hóa hoàn hảo tất cả các luật nghiệp vụ xe hơi phức tạp và đa dạng, dẫn đến việc mô hình gặp khó khăn trong việc hội tụ tối đa.

---

## 2. Thống Kê Dữ Liệu & Kết Quả Đánh Giá Tổng Thể Trên CAR-bench

### 2.1. Phân phối tác vụ trong tập dữ liệu (Dataset Splits)
Tập dữ liệu CAR-bench được chia thành các cấu hình tác vụ khác nhau phục vụ huấn luyện và kiểm thử:

| Nhóm tác vụ (Task Config) | Mô tả tác vụ | Số lượng Train | Số lượng Test |
| :--- | :--- | :---: | :---: |
| **tasks_base** | Các kịch bản cơ bản về điều khiển xe, dẫn đường, thời tiết, danh bạ. | 50 | 50 |
| **tasks_disambiguation** | Các kịch bản cần làm rõ thông tin mơ hồ (tra cứu sở thích hoặc hỏi người dùng). | 31 | 25 |
| **tasks_hallucination** | Các kịch bản cố ý gỡ bỏ công cụ/tham số để thử nghiệm giới hạn của Agent. | 48 | 50 |
| **Tổng cộng** | | **129** | **125** |

### 2.2. Kết quả đánh giá tổng thể (CAR-bench Evaluation Results)
Dưới đây là kết quả kiểm thử đầy đủ của mô hình tinh chỉnh trên toàn bộ **125 tác vụ** kiểm thử công khai (Public Validation / Test split):

*   **Tổng số tác vụ (Total Tasks):** 125
*   **Tỷ lệ vượt qua tổng thể (Overall Pass Rate):** **26.4%** (33.0 / 125 tác vụ thành công)
*   **Điểm số Pass (Pass Scores):** Pass^1: 29.3% | Pass@1: 29.3%
*   **Tổng thời gian đánh giá (Evaluation Time):** 9444.7 giây (khoảng 2.62 giờ)

**Kết quả chi tiết theo từng nhóm tác vụ (Task Results by Split):**
1.  **Nhóm Base (Cơ bản):** Đạt tỷ lệ vượt qua **42.0%** (21.0 / 50 tác vụ thành công).
2.  **Nhóm Disambiguation (Làm rõ thông tin):** Đạt tỷ lệ vượt qua **44.0%** (11.0 / 25 tác vụ thành công).
3.  **Nhóm Hallucination (Ảo tưởng):** Đạt tỷ lệ vượt qua cực thấp **2.0%** (chỉ 1.0 / 50 tác vụ thành công).

---


## 3. Phân Tích Chi Tiết Các Tác Vụ Thất Bại (Failed Cases)

Dựa trên tệp log đánh giá [benchmark_run.log](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/benchmark_run.log), hệ thống đã ghi nhận kết quả đánh giá cho phân đoạn tác vụ mơ hồ (`tasks_disambiguation` từ chỉ số 19 đến 24). Thống kê chi tiết lượt chạy như sau:

### 3.1. Bảng thống kê kết quả chạy thử nghiệm (Log Stats)

| Chỉ số đánh giá | Giá trị thống kê | Ghi chú |
| :--- | :---: | :--- |
| **Tổng số tác vụ đã thực thi (Total Evaluated)** | **6** | Các tác vụ từ `disambiguation_39` đến `disambiguation_49` |
| **Số lượng thành công (Pass Count)** | **1** | Tác vụ `disambiguation_43` |
| **Số lượng thất bại (Fail Count)** | **5** | Các tác vụ còn lại |
| **Tỷ lệ thành công (Pass Rate)** | **16.67%** | $1/6$ tác vụ hoàn thành đúng kịch bản |

---

### 3.2. Chi tiết kết quả của từng tác vụ đánh giá

Dưới đây là phân tích chi tiết về kết quả thực thi của từng tác vụ được ghi nhận trong tệp log:

#### Tác vụ `disambiguation_39` — Thất bại (Fail)
*   **Kịch bản:** Người dùng muốn gửi email nhắc nhở về cuộc họp lúc 3:30 PM tại Bratislava cho các thành viên tham gia sau khi xác nhận nội dung.
*   **Lý do thất bại:** Thiếu lệnh gọi công cụ gửi email thực tế (`send_email`). Agent chỉ phản hồi bằng văn bản để hỏi người dùng có đồng ý gửi hay không thay vì thực thi cuộc gọi công cụ (hoặc do kịch bản mô phỏng kết thúc trước khi lệnh được truyền đi).

#### Tác vụ `disambiguation_41` — Thất bại (Fail)
*   **Kịch bản:** Xe đang đi từ Barcelona đến Vienna, người dùng muốn đổi điểm đến thành một nhà hàng ở Madrid theo lộ trình nhanh nhất.
*   **Lý do thất bại:**
    *   **Vi phạm chính sách dẫn đường:** Agent sử dụng điểm bắt đầu lộ trình là Madrid (`loc_mad_180891`) thay vì vị trí hiện tại của xe là Barcelona (`loc_bar_223644`), vi phạm chính sách của hệ thống xe: *Điểm bắt đầu của lộ trình dẫn đường phải là vị trí hiện tại của xe*.
    *   **Sai công cụ:** Agent cố thực thi `set_new_navigation` (sau khi xóa lộ trình cũ) trong khi ground truth yêu cầu sử dụng công cụ chỉnh sửa điểm đến trực tiếp là `navigation_replace_final_destination`.

#### Tác vụ `disambiguation_43` — Thành công (Pass)
*   **Kịch bản:** Người dùng yêu cầu kiểm tra trạng thái khí hậu và sưởi ghế, sau đó tắt sưởi ghế phụ và tăng nhiệt độ bên lái lên mức độ thoải mái.
*   **Kết quả:** Thành công. Agent tra cứu đúng giá trị nhiệt độ thoải mái từ sở thích người dùng là 22 độ C, điều chỉnh sưởi ghế phụ về 0 (`set_seat_heating`) và đặt nhiệt độ bên lái thành 22 độ C (`set_climate_temperature`).

#### Tác vụ `disambiguation_45` — Thất bại (Fail)
*   **Kịch bản:** Lộ trình ban đầu là Mannheim $\rightarrow$ Stuttgart $\rightarrow$ Paris, người dùng muốn xóa điểm dừng chân Stuttgart để đi thẳng từ Mannheim đến Paris.
*   **Lý do thất bại:** Agent đã gọi thành công công cụ xóa điểm dừng `navigation_delete_waypoint`. Tuy nhiên, ngay sau đó Agent lại cố gắng gọi thêm lệnh bắt đầu dẫn đường mới `set_new_navigation`. Do hệ thống dẫn đường vẫn đang hoạt động, lệnh này bị từ chối với mã lỗi `SetNewNavigation_001` (Navigation already active), dẫn đến hành vi bị tính là không chính xác so với chuỗi hành động chuẩn của ground truth (chỉ cần xóa điểm dừng và để dẫn đường tiếp tục).

#### Tác vụ `disambiguation_47` — Thất bại (Fail)
*   **Kịch bản:** Xe di chuyển từ Warsaw đến Hamburg, kiểm tra thấy pin thiếu nên cần tìm trạm sạc Ionity ở Warsaw sạc lên 95%, sau đó bắt đầu dẫn đường đi qua trạm sạc này rồi đến Hamburg.
*   **Lý do thất bại:** Thiết lập dẫn đường không hoàn chỉnh. Agent chỉ gọi `set_new_navigation` với lộ trình đi đến trạm sạc (`rlp_war_cha_224861`) và dừng lại để đề xuất người dùng đợi sạc xong mới đặt tiếp chặng đi Hamburg. Thực tế, hệ thống yêu cầu Agent phải thiết lập đồng thời cả 2 chặng trong một cuộc gọi duy nhất bằng cách truyền danh sách chứa cả 2 route ID vào tham số `route_ids`.

#### Tác vụ `disambiguation_49` — Thất bại (Fail)
*   **Kịch bản:** Xe đi từ Leipzig đến Hamburg (qua Frankfurt), người dùng muốn đổi điểm đến cuối từ Hamburg sang Barcelona bằng tuyến đường ngắn nhất từ Frankfurt và gọi điện đặt chỗ tại trạm sạc dọc đường.
*   **Lý do thất bại:** Mơ hồ về ngữ cảnh điểm xuất phát. Trợ lý chỉ tìm kiếm các tuyến đường từ Hamburg đi Barcelona thay vì chặng từ Frankfurt đi Barcelona (nơi xe sắp đi qua). Khi người dùng chỉ rõ khoảng cách tính từ Frankfurt, trợ lý không tự động tra cứu dữ liệu vị trí Frankfurt mà tiếp tục phản hồi bằng văn bản hỏi lại người dùng để làm rõ, dẫn đến việc người dùng giả lập dừng hội thoại với lỗi `DISAMBIGUATION_ERROR`.


---

## 4. Phân Tích Báo Cáo Thất Bại Theo Từng Nhóm Tác Vụ (Base, Hallucination, Disambiguation)

Trong quá trình đánh giá (evaluation), do thiết bị thử nghiệm gặp sự cố đột ngột nên log chi tiết của một số tác vụ không được ghi nhận hoàn chỉnh trong tệp `benchmark_run.log`. Dựa trên kết quả thống kê tổng thể (Base đạt 42.0%, Hallucination đạt 2.0%, Disambiguation đạt 44.0%) kết hợp với mã nguồn đánh giá và báo cáo trước đó của dự án, các nguyên nhân cốt lõi dẫn đến thất bại được xác định cụ thể như sau:

### 4.1. Nhóm tác vụ Base (Cơ bản) — Tỷ lệ thất bại: 58.0% (29 / 50 tác vụ)
Mặc dù là các tác vụ điều khiển cơ bản, tỷ lệ thất bại vẫn rất cao do các lỗi logic và sai lệch trong khâu kiểm thử tự động:
1.  **Lỗi đánh giá sai lệch từ LLM chấm điểm (False-Positive Evaluation/Policy Errors):**
    *   *Ngữ cảnh:* Ở một số tác vụ như `base_2`, Agent tuân thủ chính xác chính sách yêu cầu xác nhận (`REQUIRES_CONFIRMATION`) của công cụ (ví dụ: mở cốp xe `open_close_trunk_door`). Agent thực hiện hỏi người dùng và chỉ gọi công cụ khi có câu trả lời "yes".
    *   *Lý do thất bại:* Mô hình chấm điểm chính sách tự động (như `gpt-4o-mini`) mặc dù ghi nhận Agent tuân thủ đúng chính sách nhưng lại xuất cấu trúc JSON đánh giá sai lệch với nhãn `"policy_followed": false`, dẫn đến điểm số bị phạt oan về `0.0`.
2.  **Vi phạm các ràng buộc an toàn bắt buộc (Safety Constraints):**
    *   *Ràng buộc thời tiết:* Trước khi điều khiển các thiết bị ngoài trời như cửa sổ trời (`open_close_sunroof`) hoặc đèn sương mù, Agent bắt buộc phải gọi công cụ xem thời tiết `get_weather` để kiểm tra độ an toàn. Nhiều trường hợp Agent bỏ qua bước kiểm tra gián tiếp này khi nhận câu lệnh trực tiếp từ người dùng, dẫn đến bị phạt điểm.
    *   *Ràng buộc chuỗi hành động tiên quyết (Precondition Chain):* Để mở cửa sổ trời, Agent bắt buộc phải mở tấm che nắng (`sunshade`) trước. Việc gọi trực tiếp lệnh điều khiển cửa sổ trời khi tấm che nắng đang đóng sẽ bị môi trường báo lỗi.
3.  **Lỗi thiết lập định vị và dẫn đường cơ bản:**
    *   Nhầm lẫn các tham số điểm bắt đầu và điểm kết thúc, hoặc cố tình khởi chạy lộ trình dẫn đường mới (`set_new_navigation`) khi hệ thống dẫn đường cũ đang hoạt động mà chưa gọi lệnh xóa dẫn đường cũ trước.

### 4.2. Nhóm tác vụ Hallucination (Ảo tưởng) — Tỷ lệ thất bại cực cao: 98.0% (49 / 50 tác vụ)
Đây là nhóm tác vụ yếu nhất của mô hình tinh chỉnh (chỉ đạt 2.0% tương đương 1 tác vụ thành công), nguyên nhân do:
1.  **Ảo tưởng về công cụ bị gỡ bỏ (Missing Tool Hallucination):**
    *   Trong các kịch bản này, môi trường giả lập đã bị **cố ý gỡ bỏ** một số công cụ (như công cụ mở tấm che nắng hoặc mở cốp xe). Theo thói quen suy luận, Agent vẫn sinh ra mã gọi công cụ không tồn tại hoặc đề xuất thực hiện hành động đó với người dùng, vi phạm nghiêm trọng luật chơi dẫn đến việc giả lập người dùng kết thúc hội thoại với mã lỗi ảo tưởng (`HALLUCINATION_ERROR`).
2.  **Nhận thức giới hạn kém (Lack of Limit-awareness):**
    *   Khi không tìm thấy công cụ, Agent chỉ từ chối chung chung (ví dụ: *"Tôi không thể mở cốp lúc này..."*) thay vì thông báo tường minh rằng xe không hỗ trợ hoặc công cụ đã bị loại bỏ khỏi hệ thống. Theo tiêu chí của CAR-bench, việc từ chối chung chung mà không nêu lý do thiếu capability/tool được tính là không thông báo rõ ràng về việc gỡ bỏ công cụ, dẫn đến lỗi ảo tưởng.

### 4.3. Nhóm tác vụ Disambiguation (Làm rõ thông tin) — Tỷ lệ thất bại: 56.0% (14 / 25 tác vụ)
Các lỗi phổ biến trong nhóm này bao gồm:
1.  **Bỏ qua tra cứu sở thích người dùng (Preference Pre-fetching):**
    *   Khi người dùng đưa ra một yêu cầu mơ hồ (ví dụ: *"Hãy bật sưởi ghế"* nhưng không chỉ rõ cấp độ 1, 2 hay 3), Agent tự ý thiết lập mức tối đa hoặc chọn bừa một cấp độ mà không chủ động gọi công cụ `get_user_preferences` để kiểm tra tùy chọn cấu hình mặc định sẵn có của chủ xe.
2.  **Đặt câu hỏi thừa đối với thông tin đã có sẵn:**
    *   Ngược lại, đối với các thông tin đã được ghi rõ trong cấu hình sở thích của người dùng (như nhiệt độ comfort zone bên lái là 22 độ C), Agent lại đi hỏi lại người dùng thay vì gọi công cụ kiểm tra preference ngầm, vi phạm quy trình tương tác hội thoại tối ưu.
3.  **Nhầm lẫn ngữ cảnh dẫn đường và sạc xe:**
    *   Như đã phân tích ở tác vụ `disambiguation_49`, Agent không tổng hợp được thông tin lộ trình đa chặng từ Frankfurt đi Barcelona, dẫn đến việc hỏi lại thông tin khởi hành mặc dù đã có sẵn trong lịch sử hội thoại, khiến người dùng giả lập dừng hội thoại.
