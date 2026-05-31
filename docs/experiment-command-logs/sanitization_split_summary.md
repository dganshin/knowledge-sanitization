# Sanitization split 累积汇总

本文件由 `run_sanitization_10splits.sh` 增量追加。多次运行不同 `SPLITS` 时，结果会继续写入本文件。

| Date | Commit | Run ID | Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Log dir |
|---|---|---|---:|---:|---:|---:|---:|---|
| 2026-05-31T18:18:22+08:00 | 947add3 | test_mb8_eval4_split1 | 1 | 0.391304347826087 | 0.13043478260869565 | 0.456 | 2000 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T18:29:09+08:00 | 947add3 | test_mb8_eval4_split1 | 2 | 0.1509433962264151 | 0.6981132075471698 | 0.52 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T18:39:37+08:00 | 947add3 | test_mb8_eval4_split1 | 3 | 0.7391304347826086 | 0.17391304347826086 | 0.494 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T18:50:11+08:00 | 947add3 | test_mb8_eval4_split1 | 4 | 0.5789473684210527 | 0.2894736842105263 | 0.49 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T19:00:46+08:00 | 947add3 | test_mb8_eval4_split1 | 5 | 0.375 | 0.5625 | 0.456 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T21:58:53+08:00 | 0bd924b | bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718 | 6 | 0.625 | 0.3125 | 0.484 | 500 | docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718 |
| 2026-05-31T22:10:15+08:00 | 0bd924b | bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718 | 7 | 0.20689655172413793 | 0.6896551724137931 | 0.408 | 500 | docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718 |
| 2026-05-31T22:31:08+08:00 | 0bd924b | bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921 | 8 | 0.3225806451612903 | 0.5483870967741935 | 0.454 | 500 | docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921 |
| 2026-05-31T22:42:17+08:00 | 0bd924b | bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921 | 9 | 0.0 | 1.0 | 0.506 | 500 | docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921 |
| 2026-05-31T22:53:53+08:00 | 0bd924b | bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921 | 10 | 0.3076923076923077 | 0.6923076923076923 | 0.508 | 500 | docs/experiment-command-logs/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921 |
