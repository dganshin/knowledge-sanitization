# Sanitization split 汇总

本文件由 `run_sanitization_10splits.sh` 自动生成。每完成一个 split，会追加该 split 的 K_F / K_S / K_R 结果。

## 运行配置

| 字段 | 值 |
|---|---|
| date | `2026-05-31T22:19:21+08:00` |
| commit | `0bd924b46255e7be008fe2cdb611f8196129d232` |
| base_model | `/root/autodl-tmp/models/llama-hf/7B` |
| run_id | `bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921` |
| splits | `8 9 10` |
| batch_size | `128` |
| micro_batch_size | `4` |
| num_epochs | `20` |
| eval_batch_size | `4` |
| kr_sample_seed | `42` |
| log_root | `docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921` |

## 结果表

| Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Notes |
|---:|---:|---:|---:|---:|---|
| 8 | 0.3225806451612903 | 0.5483870967741935 | 0.454 | 500 | completed |
| 9 | 0.0 | 1.0 | 0.506 | 500 | completed |
| 10 | 0.3076923076923077 | 0.6923076923076923 | 0.508 | 500 | completed |
