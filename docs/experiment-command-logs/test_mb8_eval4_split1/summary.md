# Sanitization split 汇总

本文件由 `run_sanitization_10splits.sh` 自动生成。每完成一个 split，会追加该 split 的 K_F / K_S / K_R 结果。

## 运行配置

| 字段 | 值 |
|---|---|
| date | `2026-05-31T18:05:01+08:00` |
| commit | `947add3796c56d06de5f4f4f0c80e0b823de8514` |
| base_model | `/root/autodl-tmp/models/llama-hf/7B` |
| run_id | `test_mb8_eval4_split1` |
| splits | `1 2 3 4 5` |
| batch_size | `128` |
| micro_batch_size | `8` |
| num_epochs | `20` |
| eval_batch_size | `4` |
| kr_sample_seed | `42` |
| log_root | `docs/experiment-command-logs/test_mb8_eval4_split1` |

## 结果表

| Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Notes |
|---:|---:|---:|---:|---:|---|
| 1 | 0.391304347826087 | 0.13043478260869565 | 0.456 | 2000 | completed |
| 2 | 0.1509433962264151 | 0.6981132075471698 | 0.52 | 500 | completed |
| 3 | 0.7391304347826086 | 0.17391304347826086 | 0.494 | 500 | completed |
| 4 | 0.5789473684210527 | 0.2894736842105263 | 0.49 | 500 | completed |
| 5 | 0.375 | 0.5625 | 0.456 | 500 | completed |
