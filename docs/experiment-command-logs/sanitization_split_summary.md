# Sanitization split 累积汇总

本文件由 `run_sanitization_10splits.sh` 增量追加。多次运行不同 `SPLITS` 时，结果会继续写入本文件。

| Date | Commit | Run ID | Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Log dir |
|---|---|---|---:|---:|---:|---:|---:|---|
| 2026-05-31T18:18:22+08:00 | 947add3 | test_mb8_eval4_split1 | 1 | 0.391304347826087 | 0.13043478260869565 | 0.456 | 2000 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T18:29:09+08:00 | 947add3 | test_mb8_eval4_split1 | 2 | 0.1509433962264151 | 0.6981132075471698 | 0.52 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T18:39:37+08:00 | 947add3 | test_mb8_eval4_split1 | 3 | 0.7391304347826086 | 0.17391304347826086 | 0.494 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T18:50:11+08:00 | 947add3 | test_mb8_eval4_split1 | 4 | 0.5789473684210527 | 0.2894736842105263 | 0.49 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
| 2026-05-31T19:00:46+08:00 | 947add3 | test_mb8_eval4_split1 | 5 | 0.375 | 0.5625 | 0.456 | 500 | docs/experiment-command-logs/test_mb8_eval4_split1 |
