# Hướng dẫn Vận hành Môi trường, JupyterLab và Chạy Benchmark

Tài liệu này tổng hợp toàn bộ các câu lệnh cần thiết để quản lý môi trường, khởi chạy JupyterLab, và thực hiện đánh giá (benchmark) trên dự án CAR-bench cho cả mô hình gốc và mô hình đã qua Fine-tune (SFT).

---

## 1. Quản lý Môi trường với UV (UV Package Manager)

`uv` là công cụ quản lý gói Python và môi trường ảo cực nhanh được sử dụng trong dự án này.

### Cài đặt thư viện mới vào môi trường ảo cục bộ (.venv):
```bash
# Cài đặt một gói cụ thể
uv pip install <package_name>

# Cài đặt lại PyTorch chuẩn hỗ trợ CUDA 12.1 (bỏ qua cache)
uv pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121 \
    --force-reinstall --no-cache-dir
```

### Đồng bộ hóa toàn bộ môi trường từ file cấu hình dự án:
```bash
# Tự động đọc pyproject.toml và cài các thư viện đã khai báo
uv sync
```

### Chạy các lệnh của dự án thông qua môi trường ảo:
```bash
# Đảm bảo lệnh chạy chính xác trong context của môi trường ảo cục bộ
uv run <command>
```

---

## 2. Quản lý Phiên làm việc với Tmux (Terminal Multiplexer)

`tmux` giúp chạy ngầm các tiến trình dài (như train, phục vụ model, chạy benchmark) mà không sợ bị ngắt kết nối SSH.

### Các lệnh cơ bản:
```bash
# Tạo một session mới
tmux new -s <ten_session>

# Xem danh sách các session đang hoạt động
tmux ls

# Kết nối lại vào một session đang chạy ngầm
tmux attach -t <ten_session>

# Tắt hoàn toàn một session
tmux kill-session -t <ten_session>
```

### Các phím tắt trong tmux (Nhấn Ctrl+B trước, sau đó thả ra và nhấn phím tiếp theo):
* **`Ctrl + B` rồi nhấn `D`**: Thoát ra ngoài (Detach) để tiến trình chạy ngầm.
* **`Ctrl + B` rồi nhấn `[`**: Vào chế độ Copy Mode để cuộn xem log bằng phím mũi tên hoặc con lăn chuột. Nhấn **`q`** để thoát chế độ này.

### Bật tính năng cuộn chuột trực tiếp (không cần phím tắt):
Trong terminal tmux, gõ lệnh sau để bật cuộn chuột trực tiếp:
```bash
tmux set -g mouse on
```

---

## 3. Khởi chạy JupyterLab trên Server

Để làm việc với các notebook huấn luyện và xử lý dữ liệu:

### Bước 1: Chạy JupyterLab ngầm trên Server (trong tmux hoặc terminal thường)
```bash
# Chạy jupyter lab không mở trình duyệt tự động, cho phép kết nối từ ngoài
python -m jupyterlab --no-browser --port=8888 --ip=0.0.0.0 --allow-root
```

### Bước 2: Tạo cổng kết nối (SSH Tunneling) từ máy cá nhân của bạn
Gõ lệnh này trên terminal của **máy cá nhân** (thay thế cổng `8888` nếu bị trùng, và thay thông tin SSH thật của bạn):
```bash
ssh -N -L 8888:localhost:8888 hungpv@118.138.236.136
```
Sau đó, mở trình duyệt trên máy cá nhân và truy cập: `http://localhost:8888` và nhập token bảo mật được hiển thị ở log khởi chạy trên server để kết nối.

---

## 4. Quy trình Chạy Đánh giá (Benchmark)


Benchmark CAR-bench sử dụng mô hình OpenAI `gpt-4o-mini` để đóng vai trò làm User giả lập và Bộ đánh giá luật (Policy Evaluator).

### Thiết lập API Key OpenAI thật (Bắt buộc cho cả Base và Fine-tune)
Trước khi chạy bất kỳ bài test nào, bạn phải xuất mã API OpenAI thật để chạy giả lập User:
```bash
unset OPENAI_API_BASE
export OPENAI_API_KEY="sk-proj-xxxxxx..." # Thay bằng API Key thật của bạn
```

---

### A. Chạy Benchmark cho Mô hình Gốc (Qwen/Qwen3.5-4B)

Mô hình gốc có thể gọi trực tiếp thông qua API hoặc chạy trực tiếp bằng cách chỉ định tham số agent LLM.

#### Thiết lập biến môi trường cho Agent:
```bash
export AGENT_LLM="openai/Qwen/Qwen3.5-4B"
# Nếu gọi API ngoài hoặc dịch vụ khác, hãy cấu hình các biến API liên quan
```

    --show-logs \
    --log-path output/qwen_base_full_samples.log
```

---

### B. Chạy Benchmark cho Mô hình Fine-tuned (SFT)

Vì Qwen3.5 sử dụng cấu trúc Hybrid Mamba/Attention nên không thể chạy bằng vLLM nguyên bản (bản cũ). Chúng ta khởi chạy một máy chủ trung gian qua thư viện `transformers`.

#### Bước 1: Khởi chạy Model Server (Trong tmux session `vllm_server`)
```bash
# Kích hoạt môi trường conda chứa transformers mới
conda activate carbench_env

# Chạy server cục bộ ở port 8000
export CUDA_VISIBLE_DEVICES=1
python /tmp/serve_model.py
```

#### Bước 2: Thiết lập chuyển hướng API của Agent sang local server (Trong tmux session `eval_bench`)
```bash
# 1. Đảm bảo đã unset OPENAI_API_BASE để tránh ảnh hưởng tới gpt-4o-mini
unset OPENAI_API_BASE
export OPENAI_API_KEY="sk-proj-xxxxxx..." # OpenAI key thật của bạn

# 2. Định tuyến riêng cuộc gọi của Agent sang port 8000 cục bộ
export AGENT_LLM="openai/qwen3.5-4b-sft"
export AGENT_API_BASE="http://localhost:8000/v1"
export AGENT_API_KEY="local-dummy-key"
```

#### Bước 3: Thực thi chạy Benchmark
```bash
# Di chuyển tới dự án và chạy
cd /mnt/hungpv/car_bench_sft/car_bench_notebook
uv run car-bench-run scenarios/track_1_agent_under_test/eval_custom_sft.toml \
    --output output/qwen_custom_sft_full_samples.json \
    --show-logs
```

#### Bước 4: Xuất báo cáo đánh giá dạng Markdown
```bash
python generate_report.py
```
Kết quả báo cáo so sánh chi tiết và thống kê lỗi sẽ được tạo tại **`output/evaluation_report.md`**.
