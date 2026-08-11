# CAR-Bench SFT Training & Benchmark Suite

Dự án này cung cấp toàn bộ quy trình từ sinh dữ liệu SFT chuẩn format OpenAI Chat Completions, huấn luyện tinh chỉnh mô hình Qwen 3.5 4B bằng Unsloth (LoRA / Full precision), đến đánh giá hiệu năng tự động trên tập benchmark CAR-bench với 58 công cụ điều khiển xe hơi và 19 chính sách vận hành.

---

## 1. Môi Trường & Quản Lý Gói Với `uv`

Dự án sử dụng `uv` (Fast Python Package Installer & Resolver) để quản lý phụ thuộc và môi trường ảo.

### Khởi tạo & Đồng bộ phụ thuộc:
```bash
# Đồng bộ môi trường và tự động cài đặt toàn bộ package cần thiết
uv sync
```

Môi trường ảo sẽ tự động được tạo tại `.venv`. Khi chạy các script Python, bạn có thể thực thi trực tiếp bằng:
```bash
uv run python <script_path>
```

---

## 2. Tự Động Tải Dataset Từ Hugging Face

Toàn bộ dữ liệu huấn luyện SFT đã được đóng gói và xuất bản lên Hugging Face tại kho lưu trữ:
- **Dataset Repository**: `https://huggingface.co/datasets/upwitu/carbench_sft_benchmark_data`

### Danh sách các tệp dữ liệu:
- `data/car_base_sft.jsonl`: 3.500 mẫu SFT cho Base Tasks & Safety Confirmation.
- `data/car_disambiguation_sft.jsonl`: 2.520 mẫu SFT cho Disambiguation Tasks.
- `data/car_hallucination_sft.jsonl`: 2.548 mẫu SFT cho Hallucination Tasks.
- `data/car_sft_dataset_openai.jsonl`: 8.568 mẫu tổng hợp toàn bộ 3 nhóm task.

*Lưu ý*: Các mã nguồn huấn luyện (`train_base.py`, `train_disambiguation.py`, `train_hallucination.py`) được thiết lập cơ chế tự động kiểm tra: nếu dữ liệu local chưa có, hệ thống sẽ tự động tải file tương ứng từ Hugging Face `upwitu/carbench_sft_benchmark_data`.

---

## 3. Cấu Trúc Mã Nguồn

### A. Mô-đun Sinh Dữ Liệu (`data/`)
- `data/generate_car_bench_sft_data.py`: Mã nguồn sinh 8.568 mẫu SFT chuẩn format OpenAI. Hỗ trợ 2 chế độ: `--mode simulated` (chạy offline rule-based engine, chi phí 0%) và `--mode api` (chạy qua vLLM local GPU server hoặc OpenAI API).
- `data/generation_code_documentation.md`: Báo cáo chi tiết kiến trúc code sinh dữ liệu, biểu đồ luồng Mermaid và các cơ chế xử lý lỗi.

### B. Mô-đun Huấn Luyện SFT (`llm-training/`)
- `llm-training/train_base.py` & `llm-training/train_base.sh`: Huấn luyện SFT cho nhóm Base tasks và xác nhận an toàn (Safety Confirmation).
- `llm-training/train_disambiguation.py` & `llm-training/train_disambiguation.sh`: Huấn luyện SFT cho nhóm Disambiguation tasks (ưu tiên tra cứu preference nội bộ trước khi hỏi người dùng).
- `llm-training/train_hallucination.py` & `llm-training/train_hallucination.sh`: Huấn luyện SFT cho nhóm Hallucination tasks (từ chối 1 câu lịch sự khi bị cắt giảm công cụ và chuyển đổi tính năng).
- `llm-training/pyproject.toml` & `llm-training/uv.lock`: Cấu hình phụ thuộc huấn luyện Unsloth & Transformers.

### C. Mô-đun Đánh Giá Benchmark (`scenarios/`, `src/`, `scripts/`)
- `scenarios/track_1_agent_under_test/`: Tệp cấu hình TOML chứa kịch bản đánh giá benchmark cho từng tác vụ (`benchmark_sft_hallucination.toml`, `local_base_test.toml`, `local_disambiguation_test.toml`).
- `src/track_1_agent_under_test/car_bench_agent.py`: Agent tương tác với môi trường CAR-bench, nhận instruction và gọi tool call.
- `src/evaluator/server.py`: Server đánh giá kết quả thực thi công cụ và tính điểm benchmark.
- `scripts/run_vllm_*.sh` & `scripts/run_bench_*.sh`: Kịch bản khởi chạy server vLLM và chạy benchmark tự động.

---

## 4. Hướng Dẫn Sử Dụng

### 1. Sinh dữ liệu huấn luyện:
```bash
# Chạy ở chế độ giả lập offline (0% API cost)
uv run data/generate_car_bench_sft_data.py --mode simulated

# Hoặc chạy ở chế độ API với local vLLM server
uv run data/generate_car_bench_sft_data.py --mode api --api-base http://localhost:8000/v1 --model Qwen/Qwen2.5-7B-Instruct
```

### 2. Thực thi Huấn Luyện SFT:
```bash
# Huấn luyện Base tasks
bash llm-training/train_base.sh

# Huấn luyện Disambiguation tasks
bash llm-training/train_disambiguation.sh

# Huấn luyện Hallucination tasks
bash llm-training/train_hallucination.sh
```

### 3. Khởi Chạy Benchmark Đánh Giá:
```bash
# Bước 1: Khởi chạy vLLM inference server
bash scripts/run_vllm_disambig.sh

# Bước 2: Chạy benchmark evaluator
bash scripts/run_bench_disambig.sh
```
