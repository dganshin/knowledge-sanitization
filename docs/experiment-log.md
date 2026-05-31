# 实验日志

本文件用于记录本仓库的原始实验数据。记录原则如下：

- 使用中文描述，专业术语保持英文。
- 先维护总览汇总表，再维护每个 split 的详细记录。
- `K_F / K_S` 默认记录全量结果。
- `K_R` 需要明确标注是 `sample` 还是 `full`，避免混淆。
- 后续如果继续跑 `triviaqa_2` 到 `triviaqa_10`，直接按相同结构追加。

## 1. 结果总览

### 1.1 Sanitization 结果总表

| Run ID | Date | Split | Model | Train config | K_F accuracy | K_S accuracy | K_R accuracy | K_R mode | Status | Notes |
|---|---|---:|---|---|---:|---:|---:|---|---|---|
| `sani-triviaqa1-20260531-a` | `2026-05-31` | `1` | `LLaMA-7B + LoRA` | `load_in_8bit=false, batch_size=128, micro_batch_size=4, num_epochs=20` | `0.391304347826087` | `0.21739130434782608` | pending | pending | training done, partial eval done | 当前仅完成 `K_F / K_S`；`K_R` 尚未记录 |
| `test_mb8_eval4_split1` | `2026-05-31` | `1-5` | `LLaMA-7B + LoRA` | `load_in_8bit=false, batch_size=128, micro_batch_size=8, num_epochs=20` | `0.4470651094512327` | `0.3708869435689305` | `0.4832` | `sample: split1=2000, split2-5=500` | split1-5 done | 表中为 macro average；该 run 是当前主要对照结果 |

### 1.2 Split 汇总表

| Split | Run ID | K_F | K_S | K_R | K_R mode | 备注 |
|---:|---|---:|---:|---:|---|---|
| `1` | `test_mb8_eval4_split1` | `0.391304347826087` | `0.13043478260869565` | `0.456` | `sample=2000` | 重新训练后的 split1 结果；不同于早期 `micro_batch_size=4` 单跑 |
| `2` | `test_mb8_eval4_split1` | `0.1509433962264151` | `0.6981132075471698` | `0.52` | `sample=500` | 当前 5 个 split 中 sanitization 最好 |
| `3` | `test_mb8_eval4_split1` | `0.7391304347826086` | `0.17391304347826086` | `0.494` | `sample=500` | forget 失败最明显 |
| `4` | `test_mb8_eval4_split1` | `0.5789473684210527` | `0.2894736842105263` | `0.49` | `sample=500` | forget 仍偏高 |
| `5` | `test_mb8_eval4_split1` | `0.375` | `0.5625` | `0.456` | `sample=500` | sanitization 较好但 K_F 仍不低 |
| `6` | pending | pending | pending | pending | pending |  |
| `7` | pending | pending | pending | pending | pending |  |
| `8` | pending | pending | pending | pending | pending |  |
| `9` | pending | pending | pending | pending | pending |  |
| `10` | pending | pending | pending | pending | pending |  |

### 1.3 当前 split1-5 汇总

Run ID: `test_mb8_eval4_split1`

| 汇总方式 | K_F accuracy ↓ | K_S accuracy ↑ | K_R accuracy → | 说明 |
|---|---:|---:|---:|---|
| Macro average | `0.4470651094512327` | `0.3708869435689305` | `0.4832` | 对 split1-5 简单平均 |
| Micro average | `0.40236686390532544` | `0.4319526627218935` | `0.473` | 按样本数加权；`K_R` 会被 split1 的 2000 条样本放大影响 |

当前建议优先引用 macro average。`K_R` 使用非均匀抽样：split1 为 2000 条，split2-5 为 500 条；因此 `K_R micro average` 不应作为唯一结论。

## 2. 详细记录

### 2.0 复现差异与数据重叠审计摘要

审计文档：

- [`docs/repro-gap-audit.md`](./repro-gap-audit.md)
- [`docs/data-overlap-audit.md`](./data-overlap-audit.md)

关键结论：

- 当前训练和评测链路有效：split1-5 日志显示 `trainable params=8060928`、loss 下降，并且评测日志显示 `LoRA: Active`。
- 当前 24 GB GPU 上使用 `micro_batch_size=8` + gradient accumulation 保持 `batch_size=128`，属于硬件折中，不应单独视为核心方法改变。
- 论文文字与原仓库默认代码存在重要 mismatch：论文 TriviaQA prompt 为 `Answer these questions:\nQ:...\nA:`，论文称 LoRA 作用于 MLP layers；原仓库和当前分支默认使用 `alpaca` prompt，并使用 `q_proj/v_proj/gate_proj`。
- 数据审计显示：训练 question 与 `K_F/K_S` 测试 question 没有完全字符串重叠；`K_F/K_S` 10 split raw total 为 344，但 unique question 为 182；`K_R` raw total 为 179096，但 unique question 为 9961，跨 split 高度重复。
- 因此，当前结果更适合表述为：retain 能力接近论文，但 forget/sanitization 行为尚未稳定复现；主要风险来自 paper-code mismatch、数据小样本高方差、硬件折中与训练随机性共同作用。

### 2.1 Run ID: `sani-triviaqa1-20260531-a`

基本信息：

| 字段 | 值 |
|---|---|
| Date | `2026-05-31` |
| Branch | `paper-repro` |
| Split | `triviaqa_1` |
| Train script | `run_sanitization.sh` |
| Base model | `/root/autodl-tmp/models/llama-hf/7B` |
| Output dir | `out/triviaqa_1/lora_sanitization` |

训练配置：

| 参数 | 值 |
|---|---|
| `load_in_8bit` | `false` |
| `batch_size` | `128` |
| `micro_batch_size` | `4` |
| `num_epochs` | `20` |

训练记录：

- 训练已完成。
- 已观察到最终产物：`out/triviaqa_1/lora_sanitization/adapter_model.bin`
- 本次训练通过降低 `micro_batch_size` 解决了 24 GB GPU 上的 training OOM。
- 本次训练未使用 `8-bit` 加载路径，以规避当前环境下的兼容性报错。

训练 summary：

| Metric | Value |
|---|---:|
| `train_runtime` | `312.7839` |
| `train_samples_per_second` | `34.081` |
| `train_steps_per_second` | `0.256` |
| `train_loss` | `1.5743911862373352` |
| `epoch` | `19.1` |

评测记录：

| 指标 | 值 | 样本数 | 说明 |
|---|---:|---:|---|
| `K_F accuracy` | `0.391304347826087` | `23/23` | 约等于 `9/23`，forget 侧仍有较多原答案被答出 |
| `K_S accuracy` | `0.21739130434782608` | `23/23` | 约等于 `5/23`，输出 `I don't know.` 的比例仍然偏低 |
| `K_R accuracy` | pending | pending | 当前尚未记录；后续需注明是 `sample` 还是 `full` |

输出摘录：

- [`docs/experiment-outputs/triviaqa_1_kf_ks_20260531.md`](./experiment-outputs/triviaqa_1_kf_ks_20260531.md)

当前判断：

- 当前只完成了第一个 split 的 `K_F / K_S` 结果，不能直接代表论文 10 个 split 的平均表现。
- 这一轮 run 已经证明训练链路和 forget-side 评测链路可以正常跑通。
- 当前 `K_F` 偏高、`K_S` 偏低，说明 sanitization 行为仍然较弱。
- `K_R` 由于 full 评测成本过高，后续建议优先记录 `sample` 结果，并在文档中显式标注。

### 2.2 Run ID: `test_mb8_eval4_split1`

基本信息：

| 字段 | 值 |
|---|---|
| Date | `2026-05-31` |
| Branch | `paper-repro` |
| Commit | `947add3796c56d06de5f4f4f0c80e0b823de8514` |
| Splits | `triviaqa_1` 到 `triviaqa_5` |
| Train script | `run_sanitization_10splits.sh` |
| Base model | `/root/autodl-tmp/models/llama-hf/7B` |
| Output root | `out/test_mb8_eval4_split1/` |
| Log root | `docs/experiment-command-logs/test_mb8_eval4_split1/` |

训练配置：

| 参数 | 值 |
|---|---|
| `load_in_8bit` | `false` |
| `batch_size` | `128` |
| `micro_batch_size` | `8` |
| `num_epochs` | `20` |
| `eval_batch_size` | `4` |
| `kr_sample_seed` | `42` |

评测结果：

| Split | K_F accuracy ↓ | K_S accuracy ↑ | K_R accuracy → | K_R sample size |
|---:|---:|---:|---:|---:|
| `1` | `0.391304347826087` | `0.13043478260869565` | `0.456` | `2000` |
| `2` | `0.1509433962264151` | `0.6981132075471698` | `0.52` | `500` |
| `3` | `0.7391304347826086` | `0.17391304347826086` | `0.494` | `500` |
| `4` | `0.5789473684210527` | `0.2894736842105263` | `0.49` | `500` |
| `5` | `0.375` | `0.5625` | `0.456` | `500` |

样本统计：

| Split | K_F correct / total | K_S correct / total | K_R correct / sample |
|---:|---:|---:|---:|
| `1` | `9 / 23` | `3 / 23` | `912 / 2000` |
| `2` | `8 / 53` | `37 / 53` | `260 / 500` |
| `3` | `17 / 23` | `4 / 23` | `247 / 500` |
| `4` | `22 / 38` | `11 / 38` | `245 / 500` |
| `5` | `12 / 32` | `18 / 32` | `228 / 500` |

汇总统计：

| 汇总方式 | K_F accuracy ↓ | K_S accuracy ↑ | K_R accuracy → |
|---|---:|---:|---:|
| Macro average | `0.4470651094512327` | `0.3708869435689305` | `0.4832` |
| Micro average | `0.40236686390532544` | `0.4319526627218935` | `0.473` |

输出文件：

- 每个 split 的原始 JSON 和 accuracy 文件位于 `out/test_mb8_eval4_split1/triviaqa_<split>/results/trivia_qa/`
- 命令行日志位于 `docs/experiment-command-logs/test_mb8_eval4_split1/`
- 自动汇总文件：`docs/experiment-command-logs/test_mb8_eval4_split1/summary.md`
- 累积汇总文件：`docs/experiment-command-logs/sanitization_split_summary.md`

分析：

- `K_R` 维持在约 `0.48`，说明 retain 能力没有明显崩坏，和此前预期的 retain 水平接近。
- `K_F` 和 `K_S` 在 split 间波动很大。split2 的 `K_F=0.1509`、`K_S=0.6981` 表现最好；split3 的 `K_F=0.7391`、`K_S=0.1739` 表现最差。
- 前 5 个 split 的 macro `K_F=0.4471` 仍偏高，macro `K_S=0.3709` 仍偏低，当前不能认为已复现论文级 sanitization 效果。
- split1 本次 `K_S=0.1304` 低于早期单跑的 `0.2174`，这是重新训练后的结果，可能来自训练随机性和 `micro_batch_size` 从 `4` 改为 `8` 后的优化轨迹差异。
- 当前 `K_R` 是 sample 评测，不是 full `K_R`。其中 split1 使用 2000 条，split2-5 使用 500 条；汇报时应优先使用 macro average，并明确 sample 策略。

下一步：

- 继续跑 `SPLITS="6 7 8 9 10"` 补齐后 5 个 split。
- 后续汇总 10 split 时优先报告 macro average，并单独说明 `K_R` 的 sample 策略。
- 如需进一步诊断 sanitization 弱的问题，应抽查 split3/4 的 `K_F/K_S` 生成文本，确认是继续输出原答案、输出近似拒答但 exact match 失败，还是输出其他幻觉答案。
