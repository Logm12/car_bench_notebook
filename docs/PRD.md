# Tài liệu Yêu cầu Sản phẩm (PRD) - Hệ thống Tác nhân Trợ lý Giọng nói trên Xe hơi (CAR-bench Agent)

Tài liệu này xác định các yêu cầu nghiệp vụ, kỹ thuật và thiết kế cho hệ thống tác nhân trợ lý ảo điều khiển bằng giọng nói tích hợp trong cabin xe hơi. Tác nhân này hoạt động như một thực thể được kiểm thử (Agent Under Test) trong khung đánh giá tiêu chuẩn CAR-bench.

---

## 1. Đánh giá Vấn đề

Hệ thống điều khiển cabin xe hơi hiện đại ngày càng phức tạp, yêu cầu tài xế phải thao tác thủ công trên màn hình cảm ứng hoặc các nút bấm vật lý. Việc này gây mất tập trung khi lái xe, trực tiếp làm tăng nguy cơ tai nạn giao thông. Các trợ lý ảo giọng nói hiện tại trên thị trường thường gặp phải các hạn chế sau:
- Nhận diện câu lệnh cứng nhắc, không hiểu được ngôn ngữ tự nhiên hoặc các yêu cầu lồng ghép phức tạp của hành khách.
- Dễ bị hiện tượng ảo giác (hallucination), dẫn đến việc gọi sai công cụ điều khiển thiết bị hoặc tự ý thực hiện các hành động nguy hiểm.
- Không có cơ chế kiểm soát an toàn vật lý, dẫn đến vi phạm các quy tắc cơ bản trong vận hành xe hơi (ví dụ: mở cửa sổ trời khi trời mưa, hoặc mở cửa xe khi xe đang di chuyển ở tốc độ cao).

### Sự cần thiết của dự án
Dự án CAR-bench nhằm xây dựng một tiêu chuẩn đánh giá và tối ưu hóa các tác nhân thông minh trong xe hơi. Để tham gia và đạt kết quả cao trong kỳ đánh giá này, việc phát triển một tác nhân trợ lý ảo có khả năng thực thi chính xác các công cụ điều khiển thiết bị, đồng thời tuân thủ nghiêm ngặt các chính sách an toàn là nhiệm vụ bắt buộc. Việc tối ưu hóa mô hình thông qua tinh chỉnh (Fine-tuning) và căn chỉnh hành vi (Alignment) cần được thực hiện ngay để đạt độ tin cậy cao, độ trễ thấp và khả năng chạy cục bộ trên phần cứng biên của xe mà không phụ thuộc hoàn toàn vào đám mây, giúp tối ưu hóa độ trễ và chi phí.

### Bối cảnh và Dữ liệu hỗ trợ
Các phân tích từ nhật ký chạy thử nghiệm của bộ đánh giá (Evaluator logs) cho thấy các mô hình ngôn ngữ lớn dạng nền tảng (base models) khi chưa được tinh chỉnh thường xuyên vi phạm các quy tắc an toàn vật lý của cabin. Hơn nữa, việc gọi công cụ thường xuyên bị sai tên hoặc sai cấu trúc tham số đầu vào. Giao thức A2A (Agent-to-Agent) phiên bản 1.0 hoạt động trên nền tảng HTTP JSON-RPC được xác định là giao thức kết nối tiêu chuẩn, đòi hỏi tác nhân phải xử lý chính xác cấu trúc dữ liệu dạng Part (text và data) để duy trì hội thoại đa lượt mà không gây rò rỉ bộ nhớ.

---

## 2. Tóm tắt Giải pháp

Giải pháp là xây dựng một máy chủ tác nhân ASGI (Starlette/Uvicorn) chạy cục bộ, giao tiếp trực tiếp với bộ đánh giá Evaluator thông qua giao thức A2A JSON-RPC. Tác nhân sẽ quản lý lịch sử hội thoại dựa trên mã phiên chạy (context_id), phân tích chỉ thị hệ thống chứa 19 chính sách nghiệp vụ, đọc lược đồ công cụ được cung cấp và phản hồi bằng lệnh gọi công cụ thích hợp hoặc hội thoại tự nhiên với người dùng. Hệ thống cũng đi kèm một đường ống (pipeline) huấn luyện tinh chỉnh sử dụng các kỹ thuật học ưu tiên (DPO/ORPO) để căn chỉnh hành vi của tác nhân theo đúng các chính sách an toàn mà không làm tăng độ dài prompt hay chi phí suy luận.

### Người dùng Mục tiêu
- Người dùng chính: Người lái xe và hành khách trong cabin xe thông minh (VinFast, XanhSM), những người cần sử dụng giọng nói tự nhiên để điều khiển xe một cách an toàn và rảnh tay.
- Người dùng thứ cấp: Đội ngũ kỹ sư phát triển và tối ưu hóa tác nhân (CAR-bench Agent Optimization Team), những người cần kiểm tra kết quả đánh giá, thu thập chỉ số hiệu năng để cải tiến mô hình.
- Đối tượng loại trừ: Tài liệu này không áp dụng cho các hệ thống điều khiển xe từ xa ngoài cabin hoặc các tác vụ xử lý hàng loạt không mang tính tương tác thời gian thực.

### Định nghĩa Thành công
Thành công của hệ thống được đo lường bằng các chỉ số cụ thể sau:
- Tỉ lệ Pass^3 trung bình (Average Pass^3): Đạt tối thiểu 60% trên tập đánh giá tiêu chuẩn của CAR-bench (mỗi kịch bản phải thực hiện đúng hoàn toàn trong 3 lần chạy liên tiếp).
- Tỉ lệ vi phạm chính sách an toàn (Safety Policy Violation): Đạt mức 0% tuyệt đối. Bất kỳ hành vi nào vi phạm 19 quy tắc an toàn vật lý của cabin xe đều được coi là lỗi nghiêm trọng làm thất bại kịch bản.
- Độ trễ phản hồi trung bình (Average Turn Latency): Dưới 2.0 giây cho mỗi lượt phản hồi thông qua máy chủ JSON-RPC khi chạy trên cấu hình GPU tiêu chuẩn.
- Tỉ lệ gọi sai công cụ (Tool Call Error Rate): Dưới 2% tổng số lần kích hoạt công cụ.

### Nguyên tắc Thiết kế Trải nghiệm (UX)
- An toàn vật lý tối thượng: Hệ thống ưu tiên bảo vệ an toàn cho xe và hành khách. Khi nhận được yêu cầu có tính chất nguy hiểm hoặc mập mờ, tác nhân phải từ chối thực hiện trực tiếp và đưa ra câu hỏi xác nhận lại với người dùng.
- Phản hồi tức thời: Thời gian phản hồi phải nhanh chóng để giảm thiểu thời gian chờ đợi của tài xế, tránh gây mất tập trung khi đang lái xe.
- Minh bạch hành động: Hệ thống phải thông báo rõ ràng về hành động chuẩn bị thực hiện khi gọi các công cụ nhạy cảm hoặc khi thông tin đầu vào chưa rõ ràng.
- Sử dụng tài nguyên tối ưu: Tránh lưu trữ dư thừa dữ liệu hội thoại cũ. Ngữ cảnh của mỗi phiên phải được dọn dẹp sạch sẽ ngay sau khi nhận được yêu cầu hủy phiên (cancel).

---

## 3. Phạm vi và Năng lực

Tác nhân tập trung vào việc tiếp nhận yêu cầu giao tiếp thông qua giao thức A2A JSON-RPC, phân tích và thực thi các câu lệnh điều khiển cabin mô phỏng, tuân thủ các quy tắc an toàn và tối ưu hóa hiệu năng suy luận. Việc xử lý luồng âm thanh đầu vào (audio streaming), chuyển đổi giọng nói thành văn bản (STT) và ngược lại (TTS) thuộc trách nhiệm của hạ tầng phần cứng xe hơi hoặc bộ Evaluator, không nằm trong phạm vi của tác nhân này.

### Các Năng lực Cốt lõi
- Xử lý giao thức JSON-RPC 2.0: Tiếp nhận các yêu cầu thông qua hai phương thức chính là `execute` và `cancel` tại đường dẫn `/jsonrpc`, hỗ trợ hiển thị thông tin tác nhân tại đường dẫn `/.well-known/agent-card`.
- Quản lý ngữ cảnh đa lượt: Lưu trữ lịch sử hội thoại theo từng phiên chạy dựa trên mã định danh `context_id` trong bộ nhớ đệm và giải phóng hoàn toàn khi nhận lệnh hủy để tránh tràn bộ nhớ.
- Phân tích và khớp lược đồ công cụ: Đọc định nghĩa công cụ ở lượt hội thoại đầu tiên, ánh xạ kết quả thực thi công cụ từ Evaluator ở các lượt tiếp theo để tiếp tục suy luận logic.
- Thực thi chính sách an toàn: Nhận diện và áp dụng 19 quy tắc vận hành an toàn trong cabin dựa trên nội dung system prompt được truyền vào.
- Báo cáo chỉ số lượt chạy (Turn Metrics): Tự động tính toán lượng token tiêu thụ (prompt_tokens, completion_tokens, thinking_tokens), thời gian xử lý và đính kèm vào phần dữ liệu siêu dữ liệu (metadata) của phản hồi cuối cùng.
- Đường ống huấn luyện căn chỉnh hành vi: Trích xuất lịch sử hội thoại thành công để huấn luyện SFT, và tạo các cặp dữ liệu so sánh ưu tiên (chosen/rejected) phục vụ huấn luyện DPO/ORPO.

### Kịch bản Người dùng Chi tiết (User Stories)

#### Tính năng 1: Thực thi công cụ và Tuân thủ chính sách an toàn
Tình huống kích hoạt: Người dùng ra lệnh bằng giọng nói: "Hãy mở cửa sổ trời lên".

- Nhánh xử lý thành công (Happy Path): Tác nhân kiểm tra dữ liệu thời tiết hiện tại thấy trời nắng ráo, tự động gọi công cụ điều khiển `adjust_sunroof` với tham số `state="open"`, đồng thời phản hồi bằng văn bản: "Tôi đã mở cửa sổ trời cho bạn".
- Nhánh độ tự tin thấp (Low-confidence Path): Tác nhân không truy xuất được thông tin thời tiết thực tế từ cảm biến hoặc API ngoài. Thay vì tự ý thực hiện, tác nhân hỏi lại người dùng: "Tôi không thể kiểm tra thông tin thời tiết lúc này, bạn có chắc chắn vẫn muốn mở cửa sổ trời không?" và đợi phản hồi đồng ý.
- Nhánh xử lý lỗi (Failure Path): Trời đang mưa lớn nhưng tác nhân bị ảo giác thông tin và vẫn gọi công cụ mở cửa sổ trời. Người dùng nhận thấy nước mưa lọt vào xe và ngay lập tức ra lệnh: "Đóng cửa sổ trời khẩn cấp!" để khắc phục sự cố.
- Nhánh sửa lỗi (Correction Path): Sau khi người dùng ra lệnh đóng cửa khẩn cấp, hệ thống ghi nhận chuỗi hành động lỗi này vào nhật ký sửa đổi (correction log). Dữ liệu này được chuyển thành mẫu tin bị từ chối (rejected) cho quá trình huấn luyện DPO/ORPO nhằm ngăn chặn lỗi tương tự lặp lại.

#### Tính năng 2: Giải quyết hội thoại mập mờ
Tình huống kích hoạt: Người dùng ra lệnh: "Hãy gọi điện thoại cho Nam".

- Nhánh xử lý thành công (Happy Path): Tác nhân phát hiện trong danh bạ có hai người tên Nam (Nam Anh và Nam Bùi). Tác nhân phản hồi: "Bạn muốn gọi cho Nam Anh hay Nam Bùi?". Người dùng trả lời: "Nam Anh". Tác nhân thực hiện gọi công cụ liên lạc tương ứng thành công.
- Nhánh độ tự tin thấp (Low-confidence Path): Do tiếng ồn trong cabin xe lớn, tác nhân nghe không rõ tên cụ thể. Tác nhân phản hồi: "Tôi nghe không rõ tên, có phải bạn muốn gọi cho Nam hay Lâm?" để người dùng xác nhận lại.
- Nhánh xử lý lỗi (Failure Path): Tác nhân tự ý thực hiện cuộc gọi đến Nam Bùi trong khi ý định của người dùng là gọi cho Nam Anh. Người dùng phát hiện qua âm thanh thông báo và nhấn nút hủy trên màn hình điều khiển hoặc nói "Hủy cuộc gọi".
- Nhánh sửa lỗi (Correction Path): Sau khi cuộc gọi bị hủy, người dùng nói: "Gọi cho Nam Anh cơ". Hệ thống lưu lại cặp hội thoại sửa đổi này để cải thiện khả năng trích xuất thực thể và xử lý hội thoại mập mờ của mô hình.

### Các thành phần ngoài phạm vi (Out-of-Scope)
- Tích hợp điều khiển trực tiếp phần cứng vật lý cơ khí của xe hơi (các hành động này được mô phỏng thông qua API của bộ Evaluator).
- Lọc tiếng ồn môi trường nâng cao và phân tách giọng nói của nhiều hành khách nói cùng lúc trong cabin.
- Huấn luyện trực tuyến (Online learning) thời gian thực ngay trên xe hơi trong quá trình vận hành thông thường.

---

## 4. Triển khai, Rủi ro và Câu hỏi mở

### Kế hoạch Triển khai và Các mốc phát triển
- Mốc 1: Xây dựng máy chủ ASGI và kiểm thử tương thích giao thức A2A JSON-RPC 2.0. Đạt yêu cầu khi tác nhân kết nối thành công và vượt qua các bài smoke test cơ bản của Evaluator.
- Mốc 2: Triển khai script trích xuất dữ liệu hội thoại (`extract_trajectories.py`) từ nhật ký của Evaluator. Chuẩn bị tập dữ liệu huấn luyện SFT chất lượng cao dựa trên các kịch bản thành công.
- Mốc 3: Huấn luyện tinh chỉnh SFT và áp dụng căn chỉnh ưu tiên DPO/ORPO sử dụng thư viện Unsloth nhằm tối ưu hóa bộ nhớ GPU. Đạt yêu cầu khi mô hình đạt tỉ lệ vi phạm chính sách an toàn là 0% và nâng tỉ lệ Pass^3 trung bình lên trên 60%.
- Mốc 4: Thực hiện lượng tử hóa mô hình sang định dạng GGUF Q4_K_M để chạy suy luận cục bộ, đóng gói hệ thống tác nhân vào container Docker để bàn giao và nghiệm thu toàn diện.

### Các ràng buộc và Giả định
- Ràng buộc phần cứng huấn luyện: Quy trình huấn luyện căn chỉnh hành vi không được vượt quá 15GB VRAM GPU để đảm bảo khả năng chạy ổn định trên các nền tảng đám mây miễn phí như Kaggle hoặc Google Colab (sử dụng GPU NVIDIA T4).
- Ràng buộc môi trường chạy: Tác nhân phải tương thích chéo, hoạt động ổn định trên cả hệ điều hành Windows (phát triển cục bộ) và Linux (môi trường container Docker để đánh giá).
- Giả định kỹ thuật: Các dịch vụ lưu trữ mô hình nền (Hugging Face) và các API hỗ trợ tạo sinh dữ liệu (OpenAI/Gemini) hoạt động ổn định, không bị gián đoạn kết nối trong suốt quá trình phát triển và huấn luyện.

### Rủi ro và Câu hỏi mở
- Rủi ro về độ trễ suy luận: Việc chạy mô hình ngôn ngữ lớn cục bộ trên phần cứng CPU/GPU giới hạn của xe hơi có thể khiến thời gian phản hồi vượt quá ngưỡng 2.0 giây.
  - Giải pháp giảm thiểu: Tiến hành thử nghiệm lượng tử hóa sâu hơn (ví dụ: Q3_K_S) hoặc nghiên cứu chuyển đổi sang các kiến trúc mô hình nhỏ hơn (như mô hình 3B hoặc 1B tham số) và đánh giá lại xem chất lượng phản hồi có bị suy giảm nghiêm trọng hay không.
- Rủi ro về tính bao phủ của chính sách: 19 quy tắc an toàn hiện tại có thể được mở rộng hoặc thay đổi trong các phiên bản cập nhật tương lai của CAR-bench.
  - Câu hỏi mở: Làm thế nào để cập nhật hoặc bổ sung các chính sách an toàn mới vào mô hình đã huấn luyện mà không cần thực hiện lại toàn bộ quy trình Fine-tuning từ đầu?
