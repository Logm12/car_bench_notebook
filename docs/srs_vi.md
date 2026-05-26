# Đặc tả Yêu cầu Phần mềm (SRS): Hệ thống Tác nhân Đánh giá CAR-bench (Agent Under Test)

## 1. Giới thiệu

### 1.1. Mục đích
Tài liệu này đặc tả chi tiết các yêu cầu chức năng, yêu cầu phi chức năng và giao diện ngoại vi cho hệ thống tác nhân trợ lý giọng nói trên xe hơi (Agent Under Test) tham gia đánh giá trong bộ benchmark CAR-bench. Tài liệu là căn cứ kỹ thuật để phát triển, tối ưu hóa và đánh giá chất lượng hệ thống tác nhân.

### 1.2. Phạm vi hệ thống
Hệ thống bao gồm dịch vụ web ASGI chạy cục bộ hoặc trên container, giao tiếp trực tiếp với CAR-bench Evaluator thông qua giao thức A2A 1.0 trên nền HTTP JSON-RPC. Hệ thống cũng đi kèm các kịch bản phụ trợ để trích xuất dữ liệu hội thoại và thực hiện tinh chỉnh hành vi (SFT/DPO/ORPO).

### 1.3. Định nghĩa và Từ viết tắt
- **A2A (Agent-to-Agent):** Giao thức giao tiếp chuẩn hóa giữa Evaluator và Agent Under Test.
- **SFT (Supervised Fine-Tuning):** Huấn luyện tinh chỉnh có giám sát dựa trên các hội thoại mẫu thành công.
- **DPO (Direct Preference Optimization):** Tối ưu hóa tùy chọn trực tiếp nhằm căn chỉnh hành vi mô hình theo các cặp dữ liệu đúng/sai (Chosen/Rejected).
- **ORPO (Odds Ratio Preference Optimization):** Tối ưu hóa tùy chọn theo tỷ số khả dĩ kết hợp trực tiếp trong pha SFT.
- **LoRA/QLoRA (Low-Rank Adaptation / Quantized LoRA):** Phương pháp huấn luyện tinh chỉnh mô hình ngôn ngữ lớn hiệu quả về tham số và bộ nhớ.
- **GGUF:** Định dạng lưu trữ mô hình ngôn ngữ lượng tử hóa tối ưu cho việc chạy suy luận nhẹ.

---

## 2. Mô tả Tổng quan

### 2.1. Quan hệ với các Hệ thống Khác
Tác nhân hoạt động độc lập với tư cách là một máy chủ phản hồi (Response Server). Evaluator đóng vai trò là client gửi yêu cầu (request) chứa lịch sử trò chuyện và thông tin công cụ giả lập của xe hơi, tác nhân xử lý yêu cầu và trả về lệnh gọi công cụ hoặc câu thoại phản hồi.

### 2.2. Các Ràng buộc Thiết kế và Triển khai
- **Ngôn ngữ lập trình:** Python 3.10 trở lên.
- **Hệ điều hành đích:** Tương thích chéo (Windows cho môi trường phát triển cục bộ và Linux/Docker cho môi trường đánh giá/huấn luyện đám mây).
- **Phần cứng huấn luyện:** Phải chạy ổn định trên các GPU phổ thông có dung lượng VRAM hạn chế (như NVIDIA T4 16GB hoặc L4 24GB trên Colab/Kaggle).

---

## 3. Các Yêu cầu Chức năng (Functional Requirements)

### 3.1. Phân tích Chỉ thị Hệ thống và 19 Chính sách (RF-01)
- **Mô tả:** Ở lượt hội thoại đầu tiên, tác nhân phải phân tích được System Prompt nằm trong phần văn bản gửi tới và áp dụng đầy đủ 19 chính sách nghiệp vụ.
- **Danh sách chính sách tiêu biểu:**
  1. Kiểm tra thời tiết trước khi mở cửa sổ trời (sunroof).
  2. Xác minh và làm sạch địa chỉ trước khi lập lộ trình định vị.
  3. Yêu cầu hành khách xác nhận rõ ràng trước khi thực hiện giao dịch tài chính hoặc gửi thông tin nhạy cảm ra ngoài xe.
  4. Không tự ý thực hiện các hành động điều khiển xe nguy hiểm khi xe đang di chuyển tốc độ cao (ví dụ: mở cửa xe, hạ phanh tay).

### 3.2. Phân tích Lược đồ Công cụ và Khớp kết quả (RF-02)
- **Mô tả:** Tác nhân phải đọc và lưu trữ danh sách các công cụ được định nghĩa dưới cấu trúc OpenAI Function Calling ở lượt đầu tiên.
- **Hành động:** Khi nhận được kết quả gọi công cụ (`tool_results`) ở các lượt tiếp theo, tác nhân phải khớp đúng kết quả với tên công cụ đã gọi trước đó để tiếp tục suy luận logic.

### 3.3. Duy trì Ngữ cảnh Hội thoại đa lượt (RF-03)
- **Mô tả:** Tác nhân phải theo dõi lịch sử tin nhắn của từng cuộc trò chuyện riêng biệt dựa vào thuộc tính `context_id`.
- **Hành động:** Lưu trữ lịch sử tin nhắn vào bộ nhớ đệm (RAM) và xóa sạch lịch sử của `context_id` cụ thể ngay khi nhận được tín hiệu `cancel` nhằm tránh hiện tượng tràn bộ nhớ.

### 3.4. Triển khai Giao thức A2A JSON-RPC (RF-04)
- **Mô tả:** Hỗ trợ giao thức JSON-RPC phiên bản 2.0 với các phương thức:
  - `execute`: Nhận thông tin đầu vào là một tin nhắn chứa các Part và trả về tin nhắn phản hồi của tác nhân.
  - `cancel`: Nhận yêu cầu hủy bỏ phiên chạy và thực hiện dọn dẹp bộ nhớ đệm.

### 3.5. Đóng gói Tin nhắn Phản hồi (RF-05)
- **Mô tả:** Tin nhắn phản hồi của tác nhân phải tuân thủ cấu trúc A2A 1.0:
  - Trả về `text Part` cho câu hội thoại tự nhiên với người dùng.
  - Trả về `data Part` cho lệnh gọi công cụ tuân thủ mô hình dữ liệu `ToolCallsData`.
  - Trả về `data Part` tùy chọn cho nội dung suy luận logic (`reasoning_content`) nếu mô hình hỗ trợ.

### 3.6. Thu thập Chỉ số Lượt chạy (RF-06)
- **Mô tả:** Tác nhân phải tích lũy và đính kèm thông tin Turn Metrics vào thuộc tính `Message.metadata` ở phản hồi cuối cùng của mỗi bước hội thoại (phản hồi không chứa lệnh gọi công cụ).
- **Các trường bắt buộc:** `prompt_tokens`, `completion_tokens`, `cost`, `model`, `thinking_tokens`, `num_llm_calls`, `avg_llm_call_time_ms`, `num_passes`.

---

## 4. Các Yêu cầu Phi chức năng (Non-functional Requirements)

### 4.1. Hiệu năng và Độ trễ (RNF-01)
- **Độ trễ phản hồi trung bình:** Thời gian từ lúc nhận được yêu cầu đến khi trả về phản hồi qua JSON-RPC phải nhỏ hơn 2.0 giây trên phần cứng GPU tiêu chuẩn.
- **Tính nhất quán (Reliability):** Phải vượt qua bài test Pass^3 (hoàn thành đúng tác vụ 3 lần liên tiếp) với tỉ lệ trung bình toàn hệ thống đạt trên 60%.

### 4.2. Quản lý Tài nguyên và Tránh lỗi tràn bộ nhớ (RNF-02)
- **VRAM tối đa khi huấn luyện:** Quy trình huấn luyện SFT/DPO/ORPO không được vượt quá 15GB VRAM để có thể chạy trên GPU NVIDIA T4 miễn phí.
- **Kỹ thuật tối ưu hóa:** Bắt buộc áp dụng cấu hình lượng tử hóa 4-bit (bitsandbytes), tối ưu hóa bộ nhớ Unsloth, và bộ tối ưu hóa paged AdamW (`paged_adamw_8bit`).
- **Xử lý tràn RAM hệ thống:** Khi thực hiện bước tạo dữ liệu so sánh ưu tiên hoặc huấn luyện, hệ thống phải chạy cơ chế dọn dẹp bộ nhớ đệm PyTorch (`torch.cuda.empty_cache()`) định kỳ và giải phóng các biến không sử dụng.

### 4.3. Độ bền vững và Khả năng Phục hồi (RNF-03)
- **Lưu trữ Checkpoint:** Hệ thống huấn luyện phải tự động lưu trữ trạng thái huấn luyện (checkpoint) trực tiếp lên thư mục đính kèm (Google Drive hoặc Kaggle Output) sau mỗi epoch hoặc số bước cấu hình trước.
- **Tự động khôi phục (Auto-resume):** Khi chương trình huấn luyện bị ngắt quãng do sập server hoặc mất kết nối, việc chạy lại chương trình phải tự động phát hiện checkpoint gần nhất và tiếp tục huấn luyện mà không cần bắt đầu lại từ đầu.

---

## 5. Giao diện Ngoại vi (External Interfaces)

### 5.1. Tham số dòng lệnh (CLI) khởi chạy
Máy chủ tác nhân phải hỗ trợ tối thiểu các tham số sau khi khởi chạy:
```bash
python server.py --host <IP_ADDRESS> --port <PORT_NUMBER> --agent-llm <MODEL_NAME_OR_PATH>
```

### 5.2. Biến Môi trường (Environment Variables)
- `OPENAI_API_KEY`: Khóa API phục vụ việc tạo dữ liệu preference của DPO hoặc sử dụng mô hình OpenAI làm tác nhân.
- `GEMINI_API_KEY`: Khóa API nếu sử dụng mô hình Gemini làm tác nhân hoặc mô hình tạo sinh dữ liệu.
- `HF_TOKEN`: Khóa Hugging Face để tải mô hình nền và tải lên checkpoint huấn luyện.
