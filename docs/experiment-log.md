# Experiment Log

This file is the canonical place for ongoing experiment records in this repository.

## 2026-05-31

### Run: `run_sanitization.sh` on `triviaqa_1`

Environment and configuration:

| Field | Value |
|---|---|
| Branch | `paper-repro` |
| Base model | `/root/autodl-tmp/models/llama-hf/7B` |
| Dataset split | `triviaqa_1` |
| Train script | `run_sanitization.sh` |
| `load_in_8bit` | `false` |
| `batch_size` | `128` |
| `micro_batch_size` | `4` |
| `num_epochs` | `20` |
| Output dir | `out/triviaqa_1/lora_sanitization` |

Training notes:

- Training completed successfully.
- Final artifact observed: `out/triviaqa_1/lora_sanitization/adapter_model.bin`
- Reported training summary:
  - `train_runtime = 312.7839`
  - `train_samples_per_second = 34.081`
  - `train_steps_per_second = 0.256`
  - `train_loss = 1.5743911862373352`
  - `epoch = 19.1`

Evaluation results recorded so far:

| Metric | Value | Notes |
|---|---:|---|
| `K_F accuracy` | `0.391304347826087` | `23/23` samples evaluated; approximately `9/23` correct |
| `K_S accuracy` | pending | to be appended |
| `K_R accuracy` | pending | to be appended |

Interpretation snapshot:

- This run completed without the earlier 8-bit loading error.
- Reducing `micro_batch_size` from `128` to `4` resolved the training OOM on a 24 GB GPU while preserving `batch_size=128`.
- This log entry records raw experiment facts only; cross-run comparison should be maintained separately in summary documents.
