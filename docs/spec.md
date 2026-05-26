# SPEC — Hệ thống Tác nhân Trợ lý Giọng nói trên Xe hơi (CAR-bench Agent)

**Nhóm:** CAR-bench Agent Optimization Team
**Track:** ☒ VinFast · ☐ Vinmec · ☐ VinUni-VinSchool · ☒ XanhSM · ☐ Open
**Problem statement:** Người lái xe gặp nguy cơ phân tâm và mất an toàn khi thao tác thủ công các chức năng trong xe, các trợ lý ảo hiện tại thường cứng nhắc hoặc dễ gọi sai công cụ gây nguy hiểm; hệ thống Agent được tinh chỉnh (Fine-tune) giúp hiểu lệnh giọng nói tự nhiên, tự động gọi đúng công cụ điều khiển và tuân thủ tuyệt đối 19 quy tắc an toàn vật lý.

---

## 1. AI Product Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi** | User nào? Pain gì? AI giải gì? | Khi AI sai thì sao? User sửa bằng cách nào? | Cost/latency bao nhiêu? Risk chính? |
| **Trả lời** | Khách hàng/người lái xe. Pain: Thao tác tay gây phân tâm; trợ lý ảo hiện tại dễ bị ảo giác gọi sai công cụ hoặc vi phạm chính sách an toàn. AI giúp tự động gọi công cụ chính xác và thực thi nghiêm ngặt 19 quy tắc an toàn trong cabin xe. | AI gọi sai công cụ nguy hiểm (mở phanh tay khi xe chạy) hoặc thực hiện sai giao dịch. Người dùng sửa: Sử dụng lệnh giọng nói đè (override) hoặc nhấn nút hủy khẩn cấp trên vô lăng. Hệ thống yêu cầu xác nhận đối với các tác vụ nhạy cảm. | Cost: Thấp do mô hình (7B/8B/32B) được tinh chỉnh nhẹ bằng LoRA và lượng tử hóa GGUF Q4_K_M để chạy biên cục bộ. Latency: Trả về phản hồi trung bình < 2.0s. Risk chính: Áo giác mô hình (Hallucination) và bỏ sót quy tắc an toàn. |

**Automation hay augmentation?** ☒ Automation · ☒ Augmentation
Justify: Kết hợp cả hai — Tự động hóa (Automation) các thao tác điều khiển thiết bị cơ bản để người lái không cần dùng tay, đồng thời tăng cường (Augmentation) khi gặp các yêu cầu nhạy cảm hoặc mập mờ bằng cách yêu cầu người dùng xác nhận trước khi thực thi.

**Learning signal:**
1. User correction đi vào đâu? Ghi nhận trực tiếp vào nhật ký sửa đổi hành động (correction log) khi người dùng hủy lệnh hoặc ra lệnh sửa đổi ngay sau đó.
2. Product thu signal gì để biết tốt lên hay tệ đi? Tỉ lệ Pass^3 tăng/giảm trên tập kiểm thử chuẩn hóa CAR-bench, tỉ lệ gọi sai công cụ (hallucination rate), và tần suất người dùng phải can thiệp hủy lệnh thực tế.
3. Data thuộc loại nào? ☐ User-specific · ☒ Domain-specific · ☐ Real-time · ☒ Human-judgment · ☐ Khác: ___
   Có marginal value không? Có. Mô hình cơ sở chưa quen với cấu trúc API điều khiển giả lập xe hơi và 19 quy tắc an toàn ngặt nghèo của CAR-bench, nên dữ liệu tinh chỉnh có giá trị biên cực kỳ lớn.

---

## 2. User Stories — 4 paths

### Feature: Thực thi công cụ và Tuân thủ chính sách (Tool Calling & Policy Compliance)

**Trigger:** Người dùng ra lệnh giọng nói: "Hãy mở cửa sổ trời lên".

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | Tác nhân kiểm tra thời tiết bên ngoài thấy trời nắng ráo, tự động gọi công cụ `adjust_sunroof(state="open")` và thông báo: "Tôi đã mở cửa sổ trời cho bạn". |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | Tác nhân không truy xuất được dữ liệu thời tiết thực tế, phản hồi: "Tôi không thể kiểm tra thông tin thời tiết lúc này, bạn có chắc chắn vẫn muốn mở cửa sổ trời không?" và chờ hành khách đồng ý. |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | Ngoài trời đang mưa lớn nhưng tác nhân vẫn gọi công cụ mở cửa sổ trời. Người dùng thấy nước mưa lọt vào xe, ngay lập tức ra lệnh: "Đóng cửa sổ trời khẩn cấp!" để đóng lại. |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | Người dùng ra lệnh đóng cửa và phàn nàn. Hệ thống ghi lại sự kiện này vào nhật ký lỗi (correction log) để làm dữ liệu rejected cho DPO/ORPO nhằm cải thiện mô hình. |

### Feature: Giải quyết hội thoại mập mờ (Disambiguation Conversation)

**Trigger:** Người dùng ra lệnh: "Hãy gọi điện thoại cho Nam".

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | Tác nhân phát hiện danh bạ có Nam Anh và Nam Bùi, hỏi lại: "Bạn muốn gọi cho Nam Anh hay Nam Bùi?". Người dùng trả lời: "Nam Anh". Tác nhân thực hiện cuộc gọi thành công. |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | Tác nhân nghe không rõ tên cụ thể do tiếng ồn cabin, đưa ra phản hồi: "Tôi nghe không rõ tên, có phải bạn muốn gọi cho Nam hay Lâm?" để người dùng chọn. |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | Tác nhân tự ý gọi cho Nam Bùi trong khi người dùng muốn gọi Nam Anh. Người dùng phát hiện khi nghe tiếng chuông gọi sai, bấm nút hủy cuộc gọi trên màn hình hoặc nói "Hủy cuộc gọi". |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | Người dùng sau khi hủy cuộc gọi sai nói: "Gọi cho Nam Anh cơ". Hệ thống ghi nhận cặp hội thoại sửa đổi này để cải thiện khả năng lọc thực thể và giải quyết mập mờ. |

---

## 3. Eval metrics + threshold

**Optimize precision hay recall?** ☒ Precision · ☐ Recall
Tại sao? Trong môi trường điều khiển xe hơi, việc thực thi sai công cụ hoặc vi phạm chính sách an toàn (low precision) gây ra rủi ro vật lý cực kỳ nguy hiểm. Vì vậy, hệ thống thà từ chối thực hiện và hỏi lại để làm rõ ý định (low recall) còn hơn tự ý thực hiện sai (low precision).

| Metric | Threshold | Red flag (dừng khi) |
|--------|-----------|---------------------|
| Average Pass^3 | ≥ 60% | < 50% trong tập đánh giá |
| Safety Policy Violation | 0% | > 0% (bất kỳ vi phạm an toàn vật lý nào) |
| Average Turn Latency | < 2.0 giây | > 3.0 giây |

---

## 4. Top 3 failure modes

| # | Trigger | Hậu quả | Mitigation |
|---|---------|---------|------------|
| 1 | Ảo giác công cụ (Hallucination) do câu lệnh chứa từ khóa nhiễu | Gọi sai công cụ điều khiển thiết bị hoặc tự bịa ra công cụ không tồn tại | Huấn luyện tinh chỉnh bằng DPO/ORPO với tập dữ liệu phạt (rejected) cho các hành vi ảo giác. |
| 2 | Người dùng đưa ra lệnh mập mờ lồng ghép hoặc lệnh bắc cầu phức tạp | Mô hình bỏ qua bước xác nhận hoặc tự ý suy đoán sai chính sách | Triển khai các validator cứng bằng code để kiểm tra đầu ra trước khi gửi lệnh điều khiển. |
| 3 | Quá tải tài nguyên bộ nhớ (OOM) do hội thoại quá nhiều lượt | Trợ lý ảo bị crash hoặc mất kết nối giữa chừng khi đang lái xe | Tích hợp Context Manager dọn dẹp ngữ cảnh cũ định kỳ và giới hạn tối đa số token lịch sử. |

---

## 5. ROI 3 kịch bản

|   | Conservative | Realistic | Optimistic |
|---|-------------|-----------|------------|
| **Assumption** | 5.000 chuyến xe/ngày, 90% hài lòng | 50.000 chuyến xe/ngày, 95% hài lòng | 200.000 chuyến xe/ngày, 98% hài lòng |
| **Cost** | $100/ngày chi phí vận hành máy chủ biên | $800/ngày | $2000/ngày |
| **Benefit** | Giảm 20% thời gian thao tác màn hình của tài xế | Giảm 50% thời gian thao tác, tăng điểm hài lòng | Tối ưu trải nghiệm rảnh tay hoàn toàn, tăng 5% doanh số bán xe |
| **Net** | Trải nghiệm lái xe an toàn hơn | Tăng mạnh giá trị thương hiệu và độ tin cậy | Vị thế dẫn đầu công nghệ trợ lý thông minh trên thị trường |

**Kill criteria:** Tỉ lệ xảy ra sự cố an toàn vật lý do lỗi gọi công cụ của tác nhân > 0.01% hoặc chi phí vận hành hạ tầng vượt quá hiệu quả kinh tế mang lại trong 3 tháng liên tiếp.

---

## 6. Mini AI spec (1 trang)

Sản phẩm là Hệ thống Tác nhân Trợ lý Giọng nói thông minh (Agent Under Test) tích hợp trên các dòng xe hơi thông minh (VinFast/XanhSM). 

Hệ thống giải quyết vấn đề mất tập trung của người lái xe khi phải thao tác thủ công, bằng cách tự động hóa hoàn toàn các lệnh điều khiển xe cơ bản (điều hòa, cửa sổ trời, định vị) qua ngôn ngữ tự nhiên, đồng thời bảo vệ an toàn hành khách bằng cơ chế tự hỏi lại để làm rõ các ý định mập mờ hoặc yêu cầu nhạy cảm.

Trọng tâm chất lượng của hệ thống nằm ở **Precision** (độ chính xác tuyệt đối trong gọi lệnh và tuân thủ 19 quy tắc an toàn vật lý). Việc huấn luyện tác nhân sử dụng kỹ thuật tinh chỉnh tham số hiệu quả (QLoRA) kết hợp căn chỉnh hành vi nâng cao (DPO/ORPO) dựa trên tập dữ liệu hội thoại thực tế trích xuất từ log Evaluator. 

Mô hình sau khi huấn luyện được lượng tử hóa thành định dạng GGUF Q4_K_M để chạy suy luận trực tiếp trên phần cứng cục bộ của xe hơi với độ trễ thấp dưới 2.0s và không phụ thuộc nhiều vào kết nối đám mây, đảm bảo tính liên tục và ổn định.
