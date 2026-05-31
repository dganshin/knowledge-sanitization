# Sanitization split 汇总

本文件由 `run_sanitization_10splits.sh` 自动生成。每完成一个 split，会追加该 split 的 K_F / K_S / K_R 结果。

## 运行配置

| 字段 | 值 |
|---|---|
| date | `2026-05-31T21:47:18+08:00` |
| commit | `0bd924b46255e7be008fe2cdb611f8196129d232` |
| base_model | `/root/autodl-tmp/models/llama-hf/7B` |
| run_id | `bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718` |
| splits | `6 7 8 9 10` |
| batch_size | `128` |
| micro_batch_size | `4` |
| num_epochs | `20` |
| eval_batch_size | `4` |
| kr_sample_seed | `42` |
| log_root | `docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718` |

## 结果表

| Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Notes |
|---:|---:|---:|---:|---:|---|
| 6 | 0.625 | 0.3125 | 0.484 | 500 | completed |
| 7 | 0.20689655172413793 | 0.6896551724137931 | 0.408 | 500 | completed |
