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

### 1.2 Split 汇总表

| Split | Run ID | K_F | K_S | K_R | K_R mode | 备注 |
|---:|---|---:|---:|---:|---|---|
| `1` | `sani-triviaqa1-20260531-a` | `0.391304347826087` | `0.21739130434782608` | pending | pending | 当前仅第一个 split 有记录 |
| `2` | pending | pending | pending | pending | pending |  |
| `3` | pending | pending | pending | pending | pending |  |
| `4` | pending | pending | pending | pending | pending |  |
| `5` | pending | pending | pending | pending | pending |  |
| `6` | pending | pending | pending | pending | pending |  |
| `7` | pending | pending | pending | pending | pending |  |
| `8` | pending | pending | pending | pending | pending |  |
| `9` | pending | pending | pending | pending | pending |  |
| `10` | pending | pending | pending | pending | pending |  |

## 2. 详细记录

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
