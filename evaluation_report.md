# CAR-bench Evaluation Report

This report summarizes the performance of the fine-tuned **Qwen3.5-4B SFT** model evaluated on the official CAR-bench test split.

## 1. Executive Summary

| Metric | Value |
|---|---|
| **Model** | Qwen3.5-4B-SFT |
| **Dataset Split** | test |
| **Overall Pass Rate** | **26.40%** |
| **Total Evaluation Tasks** | 0 |
| **Successful Tasks** | 0 |
| **Failed Tasks** | 0 |

---

## 2. Performance by Task Split

| Split | Total Tasks | Successful | Pass Rate | Avg Steps |
|---|---|---|---|---|

---

## 3. Failed Tasks Analysis

Below is the list of tasks that failed during the evaluation. These edge cases are prime candidates for preference-tuning (DPO/ORPO).

| Task ID | Split | Steps | Final Reward |
|---|---|---|---|
| *None! All tasks passed successfully.* | | | |

---

## 4. Full Task Results

<details>
<summary>Click to view the full list of evaluated tasks</summary>

| Task ID | Split | Status | Steps | Reward |
|---|---|---|---|---|

</details>

---

## 5. Next Steps / Insights
1. **Analyze Failure Scenarios:** Open `output/qwen_custom_sft_full_samples.json` and search for the specific `task_id` listed in Section 3 to see the conversation history and find where the model went wrong (e.g. invalid tool call syntax or incorrect state transition).
2. **Preference Alignment (DPO/ORPO):** Use the failed trajectories to build a preference dataset (chosen vs rejected) to perform Stage 2 RLHF alignment on the model.
