# CAR-bench SFT Training: Technical Documentation
# Tài Liệu Kỹ Thuật Chi Tiết Về Logic Huấn Luyện CAR-bench SFT

**Version**: 1.0.0 | **Last Updated**: 2026-08-01  
**Files**: `train_hallucination.py`, `train_disambiguation.py`  
**Model**: Qwen/Qwen3.5-4B via Unsloth | **Hardware**: NVIDIA A40 44GB

---

## Table of Contents / Mục Lục

1. [Overview / Tổng Quan](#1-overview--tổng-quan)
2. [System Initialization / Khởi Tạo Hệ Thống](#2-system-initialization--khởi-tạo-hệ-thống)
3. [Model Loading / Nạp Mô Hình](#3-model-loading--nạp-mô-hình)
4. [Data Pipeline / Quy Trình Xử Lý Dữ Liệu](#4-data-pipeline--quy-trình-xử-lý-dữ-liệu)
5. [Hallucination Training Logic](#5-hallucination-training-logic)
6. [Disambiguation Training Logic](#6-disambiguation-training-logic)
7. [Loss Masking via MultiTurnDataCollator](#7-loss-masking-via-multiturndatacollator)
8. [SFT Configuration & Training Execution](#8-sft-configuration--training-execution)
9. [Artifacts & Output / Kết Quả Đầu Ra](#9-artifacts--output--kết-quả-đầu-ra)
10. [Architecture Diagram / Sơ Đồ Kiến Trúc](#10-architecture-diagram--sơ-đồ-kiến-trúc)

---

## 1. Overview / Tổng Quan

### English
The CAR-bench training system fine-tunes the **Qwen 3.5 4B** language model on two distinct automotive assistant tasks:

- **Hallucination Task** (`train_hallucination.py`): Teaches the model to **correctly refuse** requests that require tools or parameters not available in its current environment. The model must learn to detect unavailable capabilities and issue a clear, direct refusal without hallucinating the missing functionality.

- **Disambiguation Task** (`train_disambiguation.py`): Teaches the model to **resolve ambiguous user requests** by first querying internal lookup tools (`get_*`, `check_*`, `search_*`) before asking the user for clarification. This enforces an "Internal Resolution First" policy that mirrors real-world automotive assistant behavior.

Both trainers apply **SFT (Supervised Fine-Tuning)** with trajectory shaping techniques inspired by the **Mach-Mind-4-Flash** technical report (arXiv:2607.09375), optimized for the CAR-bench evaluation framework (arXiv IJCAI 2026).

### Tiếng Việt
Hệ thống huấn luyện CAR-bench tinh chỉnh mô hình ngôn ngữ **Qwen 3.5 4B** trên hai tác vụ trợ lý ô tô riêng biệt:

- **Tác vụ Hallucination** (`train_hallucination.py`): Dạy mô hình **từ chối đúng cách** các yêu cầu đòi hỏi các công cụ (tools) hoặc tham số không có sẵn trong môi trường hiện tại. Mô hình phải học cách phát hiện khả năng thiếu và phát ra câu từ chối rõ ràng, trực tiếp mà không bịa đặt (hallucinate) chức năng bị thiếu.

- **Tác vụ Disambiguation** (`train_disambiguation.py`): Dạy mô hình **giải quyết các yêu cầu người dùng mơ hồ** bằng cách trước tiên truy vấn các công cụ tra cứu nội bộ (`get_*`, `check_*`, `search_*`) trước khi hỏi người dùng để làm rõ. Điều này thực thi chính sách "Giải Quyết Nội Bộ Trước Tiên" phản ánh hành vi trợ lý ô tô trong thực tế.

Cả hai trình huấn luyện đều áp dụng **SFT (Supervised Fine-Tuning)** với các kỹ thuật định hình quỹ đạo (trajectory shaping) lấy cảm hứng từ báo cáo kỹ thuật **Mach-Mind-4-Flash** (arXiv:2607.09375).

---

## 2. System Initialization / Khởi Tạo Hệ Thống

### English
Both training scripts perform the following initialization steps before model loading:

| Step | Code Location | Purpose |
|------|--------------|---------|
| **CUDA Pre-load** | Lines 9-21 | Pre-loads all Nvidia `.so` libraries via `ctypes.CDLL()` to prevent `bitsandbytes` loading errors on older servers |
| **Input Monkeypatch** | Line 28 | Overrides `builtins.input` with `lambda: "y"` to auto-confirm Unsloth's `trust_remote_code` interactive prompt |
| **TorchAO Compatibility** | Lines 40-53 | Patches missing PyTorch `int1-int7`/`uint1-uint7` dtypes and `_pytree.register_constant` for compatibility with older Torch versions |
| **Transformers Torchao Block** | Lines 59-63 | Disables `is_torchao_available()` in Transformers to prevent AttributeErrors during import |
| **DDP Cleanup** | Lines 74-77 | Unsets DDP environment variables (`WORLD_SIZE`, `RANK`, etc.) to ensure clean single-GPU training |
| **Memory Optimizer** | Line 80 | Sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` to reduce GPU memory fragmentation |

### Tiếng Việt
Cả hai script huấn luyện thực hiện các bước khởi tạo sau trước khi nạp mô hình:

| Bước | Vị Trí Code | Mục Đích |
|------|-------------|---------|
| **Pre-load CUDA** | Dòng 9-21 | Tải trước tất cả thư viện `.so` Nvidia qua `ctypes.CDLL()` để ngăn lỗi tải `bitsandbytes` trên server cũ |
| **Monkeypatch input** | Dòng 28 | Ghi đè `builtins.input` bằng `lambda: "y"` để tự xác nhận câu hỏi `trust_remote_code` tương tác của Unsloth |
| **Tương thích TorchAO** | Dòng 40-53 | Vá các kiểu dữ liệu PyTorch thiếu `int1-int7`/`uint1-uint7` và `_pytree.register_constant` cho các phiên bản Torch cũ |
| **Chặn Torchao** | Dòng 59-63 | Vô hiệu hóa `is_torchao_available()` trong Transformers để ngăn AttributeError khi import |
| **Dọn DDP** | Dòng 74-77 | Xóa các biến môi trường DDP để đảm bảo huấn luyện single-GPU sạch |
| **Tối ưu bộ nhớ** | Dòng 80 | Đặt `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` để giảm phân mảnh bộ nhớ GPU |

---

## 3. Model Loading / Nạp Mô Hình

### English
The base model is loaded using Unsloth's `FastLanguageModel.from_pretrained()` with 4-bit quantization:

```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen3.5-4B",
    max_seq_length=16384,       # Extended context for enriched system prompts + multi-turn tool conversations
    dtype=torch.bfloat16,       # BF16 precision for A40 GPU
    load_in_4bit=True,          # 4-bit quantization for memory efficiency
    trust_remote_code=True
)
```

**LoRA Configuration** (applied after loading):
```python
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                           # LoRA rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,                  # Scaling factor = lora_alpha / r = 1.0
    lora_dropout=0,                 # No dropout for Unsloth efficiency
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)
```

**Important Notes:**
- `max_seq_length=16384` was increased from 8192 to accommodate enriched system prompts and long multi-turn tool conversations
- The tokenizer is extracted with a fallback in case a `Processor` object is returned (for Qwen3-VL compatibility)
- `eos_token` is forced to `<|im_end|>` to bypass vocabulary check errors in SFTTrainer

### Tiếng Việt
Mô hình cơ sở được nạp bằng `FastLanguageModel.from_pretrained()` của Unsloth với lượng tử hóa 4-bit:

Các điểm quan trọng:
- `max_seq_length=16384` được tăng từ 8192 để chứa các system prompt được làm giàu và các cuộc hội thoại công cụ đa lượt dài
- Tokenizer được trích xuất với fallback để xử lý trường hợp đối tượng `Processor` được trả về (tương thích Qwen3-VL)
- `eos_token` bị buộc phải là `<|im_end|>` để bỏ qua lỗi kiểm tra từ vựng trong SFTTrainer

---

## 4. Data Pipeline / Quy Trình Xử Lý Dữ Liệu

### English

The data pipeline follows a **two-pass architecture** designed to build policy-to-tool mappings before processing each sample:

#### Dataset Source
- **Repository**: `upwitu/trash_draft_am` (private HuggingFace dataset)
- **Hallucination files**: `*hallucination*.jsonl` (e.g., `interactive_agent_hallucination.jsonl`, `search_hallucination.jsonl`)
- **Disambiguation files**: `*disambiguation*.jsonl` (e.g., `interactive_agent_disambiguation.jsonl`, `search_disambiguation.jsonl`)
- **Field priority**: `augmented_messages` > `raw_messages` (augmented contains reduced-capability tool scenarios)

#### Key Data Structures per Sample
Each JSONL record contains:
- `tools`: List of tool schemas available to the model (reduced for hallucination tasks)
- `augmented_messages`: Pre-processed conversation with reduced tool capability
- `raw_messages`: Original conversation with full tool capability

#### Pass 1: Policy-to-Tool Mapping (Hallucination only)
Scans all samples to build two lookup tables:
- `policy_to_all_tools`: Maps `policy_header → set(all tool names)` across all samples sharing the same policy
- `policy_tool_to_all_params`: Maps `policy_header → {tool_name → set(all param names)}`

**Policy Header Extraction**:
1. Looks for the first `# Header` line in the system message (excluding generic headers like `# Tools`, `# Instructions`)
2. **Fallback** (for XML-based policy samples): Uses `frozenset` of tool names as key, formatted as `TOOLS_KEY:tool1,tool2,...`

This two-pass design enables per-sample detection of **removed tools** (tools present in the policy's full toolset but absent from this specific sample's `tools` list) and **removed parameters** (parameters present in other samples of the same policy but absent here).

#### Pass 2: Sample Enrichment & Formatting
For each sample:
1. Parse `augmented_messages` → list of message dicts
2. Clean `<think>...</think>` blocks from assistant content
3. Normalize `None` content in assistant turns to `""`
4. **Deduplicate** via `hash(json.dumps(messages, sort_keys=True))`
5. Run `sanitize_sample()` logic filter
6. Run `has_tool_loop()` loop filter
7. Apply **task-specific trajectory shaping** (see Sections 5 & 6)
8. Apply `enrich_system_prompt()` 
9. Parse JSON-encoded `arguments` strings to dicts (Qwen3.5 Jinja2 compatibility)
10. Strip `... [truncated N chars]` markers from tool response content
11. Apply `tokenizer.apply_chat_template()` with `enable_thinking=False`
12. Filter out sequences exceeding `16384` tokens

### Tiếng Việt

Pipeline dữ liệu theo kiến trúc **hai lượt** được thiết kế để xây dựng ánh xạ policy-to-tool trước khi xử lý từng mẫu.

**Lượt 1 (Pass 1)**: Quét tất cả các mẫu để xây dựng bảng tra cứu `policy_to_all_tools` và `policy_tool_to_all_params`, phát hiện các tool và tham số bị xóa khỏi từng mẫu hallucination.

**Lượt 2 (Pass 2)**: Xử lý từng mẫu với pipeline: phân tích cú pháp → làm sạch → trùng lặp → lọc → định hình quỹ đạo → làm giàu system prompt → format chat template.

---

## 5. Hallucination Training Logic

### English

The hallucination trainer implements the **Mach-Mind-4-Flash RL Trajectory Shaping** strategy:

#### 5.1 sanitize_sample() — Logic Sanity Filter
Drops samples that violate these rules:
- Empty assistant turns with no `tool_calls` (prevents learning from no-op turns)
- Samples where the assistant claims to have "sent a verification code" but no `verify_*` or `auth_*` tool exists in the schema
- Samples where the assistant says "transferring you" but no `transfer_*` tool was actually called
- Multi-service escalation scenarios without a corresponding transfer tool call

> **Design Note**: Unlike a naive filter, this sanitizer does NOT drop samples where the assistant calls removed tools. Those are valid hallucination examples that will be handled by trajectory shaping below.

#### 5.2 System Prompt Enrichment
When removed tools or parameters are detected, the system prompt is enriched with:

```
- TOOL CALLING RULES: Do NOT call the same tool repeatedly...
- CRITICAL REFUSAL POLICY:
    The following capabilities/parameters are UNAVAILABLE:
      - Unavailable tools: [list]
      - Unavailable parameters: [list]
    If asked, respond with a STRICT DIRECT REFUSAL. Do NOT ask clarifying questions...
```

This enrichment explicitly signals to the model which capabilities are missing, teaching it to cross-reference available tools before acting.

#### 5.3 Trajectory Shaping — Diverse Refusal Rewriting
The core innovation: when an assistant turn is detected as a **hallucination** (it calls a removed tool via `tool_calls` or via Hermes XML text), the turn is **rewritten** into a refusal using one of 16 diverse templates, then all subsequent turns are truncated.

**Hallucination Detection** (per assistant turn):
1. Check `tool_calls` array for tool names in `removed_tools`
2. Check `tool_calls` for parameter names in `removed_params`
3. Check text content for `<function=tool_name>` or `"name": "tool_name"` patterns

**Refusal Template Selection**:
```python
refusal_tmpl = random.Random(conv_hash + turn_idx).choice(REFUSAL_VARIATIONS)
msg["content"] = refusal_tmpl.format(reason=reason_str)
```

The template is selected **deterministically** based on `conv_hash + turn_idx`, ensuring reproducibility across runs while achieving diversity across the dataset.

**16 Diverse Refusal Templates** (sampled):
- `"I cannot perform this action because the {reason} is unavailable in this environment."`
- `"Regrettably, I lack the {reason} needed to process this action."`
- `"I must decline this action since the {reason} is unavailable in this environment."`
- *(+ 13 more variants)*

This diversity prevents the model from overfitting to a single refusal phrase and instead forces it to learn the **concept** of unavailability.

### Tiếng Việt

#### 5.1 Bộ Lọc Sanity `sanitize_sample()`
Loại bỏ các mẫu vi phạm quy tắc logic: lượt assistant rỗng không có tool_calls, assistant tuyên bố gửi mã xác minh nhưng không có tool xác minh, v.v. **Lưu ý thiết kế**: Bộ lọc này KHÔNG loại bỏ các mẫu assistant gọi tool bị xóa — đây là các ví dụ hallucination hợp lệ được xử lý bởi trajectory shaping.

#### 5.2 Làm Giàu System Prompt
Khi phát hiện tool hoặc tham số bị xóa, system prompt được bổ sung danh sách "UNAVAILABLE" và chỉ thị từ chối trực tiếp, không hỏi lại.

#### 5.3 Định Hình Quỹ Đạo — Viết Lại Từ Chối Đa Dạng
Khi phát hiện lượt assistant gọi tool bị xóa, lượt đó được **viết lại** bằng một trong 16 mẫu từ chối đa dạng, và tất cả các lượt tiếp theo bị cắt bỏ. Template được chọn **tất định** (deterministic) theo `conv_hash + turn_idx` đảm bảo tái lập được nhưng vẫn đa dạng. Điều này ngăn model overfit vào một mẫu câu cố định.

---

## 6. Disambiguation Training Logic

### English

#### 6.1 Tool Name Hallucination Correction (Step 1)
Before any other processing, `shape_disambiguation_trajectory()` **corrects hallucinated tool names** in assistant turns by:
1. Building `valid_tool_names` from the sample's `tools` schema
2. For each `tool_calls` entry: if the name is NOT in `valid_tool_names`, attempt fuzzy matching
3. **Fuzzy matching rules**:
   - `"vehicle"` in both the called name and a valid name → use the valid name
   - `"status"` in both → use the valid name
4. Invalid names with no fuzzy match are silently dropped from `tool_calls`

**Example fix**: `get_vehicle_state` → `get_vehicle_status` (or whatever the schema actually defines)

#### 6.2 Internal Resolution First (Step 2 — Trajectory Shaping)
This enforces the CAR-bench disambiguation policy at the **data level**:

```
IF assistant asks clarification question BEFORE any tool call:
    AND lookup tools (get_*, check_*, search_*, fetch_*, query_*, list_*) are available:
    THEN:
        → Replace question turn with a tool call to lookup_tools[0]
        → Insert synthetic tool response: {"status": "success", "result": "Internal state/preferences checked."}
        → Mark made_tool_call = True, stop shaping
```

This teaches the model that the **first response** to ambiguity should always be an internal lookup, not a user-facing question.

#### 6.3 System Prompt Enrichment
The disambiguation system prompt is enriched with two rules:
1. **Anti-loop rule**: Same as hallucination — prevents repeated tool calls
2. **CAR-BENCH DISAMBIGUATION POLICY**: Explicit two-level resolution strategy:
   - Level 1: Internal resolution via available tools (get_user_preferences, get_vehicle_status, etc.)
   - Level 2 (fallback only): Ask user when internal data is unavailable

#### 6.4 Key Differences vs Hallucination
| Aspect | Hallucination | Disambiguation |
|--------|---------------|----------------|
| **Primary learning target** | Detect & refuse missing tools | Prefer internal lookup before asking user |
| **Trajectory rewriting** | Replace hallucinated call with refusal | Replace early question with lookup call |
| **System prompt enrichment** | Lists UNAVAILABLE tools/params | Lists 2-level resolution policy |
| **Tool name correction** | N/A | Fuzzy-match hallucinated tool names |
| **Data source** | `*hallucination*.jsonl` | `*disambiguation*.jsonl` |

### Tiếng Việt

#### 6.1 Sửa Tên Tool Hallucination (Bước 1)
`shape_disambiguation_trajectory()` sửa tên tool bị hallucinate trong lượt assistant bằng cách đối chiếu với schema tool hợp lệ. Nếu không khớp chính xác, dùng fuzzy matching theo từ khóa `"vehicle"`, `"status"`. Tên không hợp lệ và không có fuzzy match sẽ bị loại khỏi `tool_calls`.

#### 6.2 Giải Quyết Nội Bộ Trước Tiên (Bước 2 — Định Hình Quỹ Đạo)
Nếu assistant hỏi người dùng trước khi gọi bất kỳ tool nào, và có sẵn các tool tra cứu nội bộ (`get_*`, `check_*`, v.v.), thì lượt hỏi đó được **thay thế** bằng một lệnh gọi tool tra cứu, kèm một lượt phản hồi tổng hợp. Điều này dạy mô hình luôn ưu tiên tra cứu nội bộ trước khi hỏi người dùng.

---

## 7. Loss Masking via MultiTurnDataCollator

### English

Both trainers implement a custom `MultiTurnDataCollator` that **only computes loss on assistant response tokens**, masking out system prompt tokens, user tokens, and tool output tokens.

#### Algorithm
```
For each sample in batch:
    1. Initialize all labels to -100 (masked)
    2. Find <|im_start|>assistant marker positions
    3. For each assistant segment [start, end]:
        a. Skip past <think>...</think> block if present (up to +20 tokens lookahead)
        b. Unmask labels[actual_start : end] = input_ids[actual_start : end]
    4. Repeat until no more assistant segments
```

#### Key Design Decisions
- **Token boundary**: Uses `<|im_start|>assistant` (without trailing `\n`) to avoid tokenizer merging issues specific to Qwen tokenizer
- **Think-block skipping**: Looks ahead up to 20 tokens for `</think>` token IDs to skip empty `<think></think>` blocks that Unsloth emits when `enable_thinking=False`
- **Multi-turn awareness**: The while-loop correctly handles multi-turn conversations by searching forward from the previous segment's end
- **`<|im_end|>` inclusion**: The end marker token is included in the loss (it IS the EOS signal the model must learn to generate)

#### Why This Matters
Training without loss masking would teach the model to predict all tokens, including system prompt contents and tool execution results — leading to poor generalization. The custom collator ensures the model only learns **what to say as the assistant**, not to memorize the prompts.

### Tiếng Việt

Cả hai trình huấn luyện triển khai `MultiTurnDataCollator` tùy chỉnh chỉ tính loss trên các token phản hồi của assistant.

**Thuật toán**: Với mỗi mẫu trong batch, khởi tạo tất cả nhãn là -100 (masked), tìm các vị trí marker `<|im_start|>assistant`, bỏ qua các block `<think>...</think>` rỗng, rồi bỏ mask các nhãn từ vị trí bắt đầu thực sự đến cuối lượt assistant (bao gồm cả `<|im_end|>`).

**Lý do quan trọng**: Không có loss masking, mô hình sẽ học dự đoán tất cả token kể cả nội dung system prompt và kết quả thực thi tool, dẫn đến tổng quát hóa kém. Collator tùy chỉnh đảm bảo mô hình chỉ học **cách phản hồi với tư cách assistant**.

---

## 8. SFT Configuration & Training Execution

### English

```python
SFTConfig(
    dataset_text_field="text",
    output_dir=PERSISTENT_DIR,
    learning_rate=3e-5,                      # Tuned for stronger learning signal
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,           # Effective batch size = 2 * 8 = 16
    per_device_eval_batch_size=1,
    num_train_epochs=2.0,                    # 2 full passes over 14K+ samples
    max_steps=3 if smoke_test else -1,       # Quick validation mode
    weight_decay=0.02,
    lr_scheduler_type="cosine",              # Smooth LR decay
    warmup_ratio=0.03,
    bf16=True,
    optim="adamw_8bit",                      # 8-bit Adam for memory efficiency
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=1,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    packing=False,                           # Disabled to avoid cross-sample contamination
    max_seq_length=16384
)
```

**Training Results (Disambiguation)**:
- `eval_loss`: 0.2374 (Epoch 2)
- `train_loss`: 0.2636
- Total runtime: ~26.4 hours (94,000s)

### Tiếng Việt

Cấu hình SFT sử dụng `learning_rate=3e-5` với cosine scheduler, 2 epochs, batch size hiệu quả 16 (2 × 8 gradient accumulation steps). Tối ưu hóa 8-bit Adam để tiết kiệm bộ nhớ. `packing=False` để tránh ô nhiễm cross-sample.

---

## 9. Artifacts & Output / Kết Quả Đầu Ra

### English

| Artifact | Path | Description |
|---------|------|-------------|
| **LoRA Adapter** | `./outputs_*/sft_lora_adapter/` | Lightweight adapter weights (~82MB) |
| **Merged Model (16-bit)** | HuggingFace Hub | Full 16-bit merged weights (~9GB) |
| **Loss Plot** | `./outputs_*/loss_plot.png` | Train vs. Eval loss curve |
| **Best Checkpoint** | `./outputs_*/checkpoint-*/` | Best model checkpoint by `eval_loss` |

**Published Models**:
- Hallucination: [`dragonstorm123/qwen3.5-4b-sft-hallucination`](https://huggingface.co/dragonstorm123/qwen3.5-4b-sft-hallucination)
- Disambiguation: [`dragonstorm123/qwen3.5-4b-sft-disambiguation`](https://huggingface.co/dragonstorm123/qwen3.5-4b-sft-disambiguation)

**vLLM Serving** (post-training):
```bash
vllm serve dragonstorm123/qwen3.5-4b-sft-hallucination \
    --served-model-name hallucination \
    --port 8300 \
    --max-model-len 4096 \
    --tool-call-parser hermes \
    --reasoning-parser qwen3 \
    --default-chat-template-kwargs '{"enable_thinking": false}'
```

### Tiếng Việt
Sau training, LoRA adapter (~82MB) được lưu cục bộ. Mô hình 16-bit hợp nhất được đẩy trực tiếp lên Hugging Face Hub để phục vụ benchmark. vLLM serve model với các tham số đặc biệt để tắt chế độ thinking và kích hoạt parse tool call đúng định dạng Hermes.

---

## 10. Architecture Diagram / Sơ Đồ Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────────┐
│               CAR-bench SFT Training Pipeline                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [HuggingFace Hub: upwitu/trash_draft_am]                          │
│       ├── interactive_agent_hallucination.jsonl                     │
│       ├── search_hallucination.jsonl                                │
│       ├── interactive_agent_disambiguation.jsonl                    │
│       └── search_disambiguation.jsonl                               │
│              │                                                      │
│              ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  PASS 1 (Hallucination only)                        │           │
│  │  Build policy_to_all_tools & policy_tool_to_params  │           │
│  │  Key: "# PolicyName" OR "TOOLS_KEY:t1,t2,..."      │           │
│  └──────────────────────┬──────────────────────────────┘           │
│                          │                                          │
│              ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  PASS 2 — Per Sample Processing                     │           │
│  │  1. Parse augmented_messages                        │           │
│  │  2. Clean <think> blocks                            │           │
│  │  3. Deduplication (conv_hash)                       │           │
│  │  4. sanitize_sample() filter                        │           │
│  │  5. has_tool_loop() filter                          │           │
│  │  6. Task-specific Trajectory Shaping ──────────┐   │           │
│  │  7. enrich_system_prompt()                      │   │           │
│  │  8. apply_chat_template(enable_thinking=False)  │   │           │
│  │  9. Token length filter (>16384 → skip)         │   │           │
│  └─────────────────────────────────────────────────┘   │           │
│                                                          │           │
│  ┌───────────────────────────────┐ ┌────────────────────┘           │
│  │  HALLUCINATION Shaping        │ │  DISAMBIGUATION Shaping        │
│  │  Detect removed tool calls    │ │  1. Fix hallucinated tool names│
│  │  → Rewrite with 1 of 16       │ │     via fuzzy matching         │
│  │    diverse refusal templates  │ │  2. Replace early user question│
│  │  → Truncate subsequent turns  │ │     with internal lookup call  │
│  └───────────────────────────────┘ └────────────────────────────────│
│                                                                     │
│              ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Model Training                                     │           │
│  │  Base: Qwen/Qwen3.5-4B (4-bit, BF16)               │           │
│  │  Adapter: LoRA r=16, alpha=16                       │           │
│  │  Loss: MultiTurnDataCollator                        │           │
│  │        (only assistant tokens, masks system/user)   │           │
│  │  Config: 2 epochs, lr=3e-5, cosine, BS=16           │           │
│  └─────────────────────────────────────────────────────┘           │
│              │                                                      │
│              ▼                                                      │
│  LoRA Adapter saved → push_to_hub_merged(16bit) → HF Hub           │
│                                                                     │                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference / Tham Khảo Nhanh

### Running Training / Chạy Huấn Luyện
```bash
# Hallucination Task
CUDA_VISIBLE_DEVICES=1 bash /mnt/hungpv/car_bench_notebook/llm-training/train_hallucination.sh

# Disambiguation Task  
CUDA_VISIBLE_DEVICES=1 bash /mnt/hungpv/car_bench_notebook/llm-training/train_disambiguation.sh

# Smoke test (3 steps, no save)
CUDA_VISIBLE_DEVICES=1 bash train_hallucination.sh --smoke-test
```

### Running Benchmark / Chạy Benchmark
```bash
# Start vLLM server
CUDA_VISIBLE_DEVICES=0 bash /mnt/hungpv/car_bench_notebook/scripts/run_vllm_hallu.sh

# In another terminal, run CAR-bench evaluation
export OPENAI_API_KEY="your-key"
bash /mnt/hungpv/car_bench_notebook/scripts/run_bench_hallu.sh
```

---

*Documentation generated following `@my-skills/code-documentation-doc-generate` guidelines.*  
*Tài liệu được tạo theo hướng dẫn `@my-skills/code-documentation-doc-generate`.*
