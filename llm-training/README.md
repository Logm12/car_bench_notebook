# CAR-Bench SFT Training & Benchmark Suite — Training Module

Mô-đun huấn luyện SFT hỗ trợ fine-tuning mô hình Qwen 3.5 4B bằng Unsloth trên các tác vụ CAR-bench. Dữ liệu huấn luyện sẽ được tự động tải từ Hugging Face dataset `upwitu/carbench_sft_benchmark_data` nếu không tìm thấy tệp local.

---

## 1. Đồng Bộ Phụ Thuộc Với `uv`

```bash
uv sync
```

---

## 2. Hướng Dẫn Chạy Huấn Luyện

### A. Base & Safety Confirmation Tasks SFT
```bash
bash llm-training/train_base.sh
```

### B. Disambiguation Tasks SFT
```bash
bash llm-training/train_disambiguation.sh
```

### C. Hallucination Tasks SFT
```bash
bash llm-training/train_hallucination.sh
```

---

## 3. Cấu Trúc Các Tệp Tin

- `train_base.py` & `train_base.sh`: Huấn luyện tác vụ Base & Safety Confirmation.
- `train_disambiguation.py` & `train_disambiguation.sh`: Huấn luyện tác vụ Disambiguation.
- `train_hallucination.py` & `train_hallucination.sh`: Huấn luyện tác vụ Hallucination.
- `upload_disambiguation.py` & `upload_hallucination.py`: Upload LoRA adapter và merged model 16-bit lên Hugging Face Hub.
