# 当前结果分析与后续讨论说明

更新日期：`2026-06-01`

本文用于总结当前 `paper-repro` 分支的实验结果、主要异常、当前可以得出的结论，以及后续最值得做的实验。详细原始记录见：

- [`docs/experiment-log.md`](./experiment-log.md)
- [`docs/repro-gap-audit.md`](./repro-gap-audit.md)
- [`docs/data-overlap-audit.md`](./data-overlap-audit.md)
- [`docs/rescore-analysis.md`](./rescore-analysis.md)

## 1. 当前已经完成的实验

### 1.1 Sanitization 10 split

当前已经完成原仓库默认实现适配版的 LLaMA-7B Sanitization 10 split：

- 训练：`K_S + K_R`
- `K_F/K_S`：full eval
- `K_R`：sample eval
- base model：`/root/autodl-tmp/models/llama-hf/7B`
- `load_in_8bit=false`
- `batch_size=128`
- split1-5：`micro_batch_size=8`
- split6-10：`micro_batch_size=4`
- `num_epochs=20`

10 split macro 结果：

| 指标 | 当前结果 | 论文参考 | 方向 | 判断 |
|---|---:|---:|---|---|
| `K_F` | `36.97%` | 约 `7.0%` | 越低越好 | 明显偏高，遗忘不足 |
| `K_S` | `50.97%` | 约 `74.3%` | 越高越好 | 有 sanitization 学习，但不足 |
| `K_R sample` | `47.76%` | 约 `49.8%` | 接近 Orig/论文 | 基本接近论文 retain 水平 |

10 split micro 结果：

| 指标 | Micro result | 样本统计 |
|---|---:|---|
| `K_F` | `34.30%` | `118 / 344` |
| `K_S` | `54.07%` | `186 / 344` |
| `K_R sample` | `47.26%` | `3072 / 6500` |

### 1.2 Orig baseline K_F/K_S

Orig baseline 已完成 `K_F/K_S` full eval：

- 原始 LLaMA-7B
- 不训练
- 不加载 LoRA
- `--no_peft --lora_weights no-lora`
- `K_R` 暂未正式跑完，当前只记录 `K_F/K_S`

严格 exact-match 结果：

| 指标 | Orig strict result |
|---|---:|
| `K_F` | `0.00%` |
| `K_S` | `0.00%` |

这个结果需要谨慎解释。它不代表原模型完全不会回答原答案，而是暴露了当前评测的 answer extraction 问题。

## 2. 当前最重要的发现

### 2.1 Retain 没明显崩，sanitization 没完全复现

当前最直接的结论：

- `K_R sample = 47.76%`，接近论文 LLaMA Sanitization 的 retain 约 `49.8%`。
- 说明 LoRA sanitization 后，普通知识保留没有明显崩坏。
- 但 `K_F = 36.97%` 明显高于论文约 `7.0%`。
- `K_S = 50.97%` 低于论文约 `74.3%`。
- 因此当前不能说已经复现论文效果。

更准确的说法：

> 当前链路已经跑通，retain 侧接近论文，但 forget/sanitization 侧没有稳定达到论文报告水平。

### 2.2 Split 差异非常大

10 个 split 的表现差异明显：

| Split | K_F ↓ | K_S ↑ | K_R sample |
|---:|---:|---:|---:|
| 1 | 39.13% | 13.04% | 45.60% |
| 2 | 15.09% | 69.81% | 52.00% |
| 3 | 73.91% | 17.39% | 49.40% |
| 4 | 57.89% | 28.95% | 49.00% |
| 5 | 37.50% | 56.25% | 45.60% |
| 6 | 62.50% | 31.25% | 48.40% |
| 7 | 20.69% | 68.97% | 40.80% |
| 8 | 32.26% | 54.84% | 45.40% |
| 9 | 0.00% | 100.00% | 50.60% |
| 10 | 30.77% | 69.23% | 50.80% |

明显现象：

- split9 几乎是理想结果：`K_F=0`、`K_S=1`。
- split2/7/10 表现较好。
- split3/4/6 明显失败，`K_F` 高、`K_S` 低。

这说明方法对 forgetting target、split、训练随机性或 prompt 非常敏感。后续不能只看总平均，需要做 split-level 和 target-level 诊断。

### 2.3 Orig strict K_F=0 是评测问题，不是模型一定没泄露

Orig baseline 的严格 exact-match 全 0，但抽查生成文本发现，原模型经常输出类似：

```text
Paris

### Instruction:

### Input:
...
```

也就是说模型先输出了正确原答案，然后继续续写了 Alpaca prompt。当前 `task.py` 的 exact-match 会把整段 `model_response` 和 gold alias 比较，因此这类输出会被判错。

诊断统计：

| Orig 诊断口径 | K_F | K_S |
|---|---:|---:|
| 当前严格 exact-match | 0.00% | 0.00% |
| response 包含 gold alias | 38.66% | 0.00% |
| 截断到下一个 `### Instruction:` 后 exact-match | 13.95% | 0.00% |

解释：

- Orig 不会自然输出 `I don't know.`，这点比较明确。
- Orig 会泄露一些原答案，但当前 strict exact-match 低估了泄露。
- Sanitization 的 `K_F` 和 Orig strict `K_F` 不能直接做简单差值解释。

### 2.4 Post-hoc re-score 后的判断

已新增 `scripts/rescore_triviaqa_outputs.py`，只读取现有 JSON，不重新跑模型。它同时报告：

- `current_strict`：当前 `task.py` 口径；
- `first_line`：截断到第一行；
- `before_next_instruction`：截断到下一个 `### Instruction:`；
- `paper_like`：近似论文 TriviaQA 描述，优先按第一处换行截断，否则按最后一个终止标点截断；
- `contains_alias`：只作为泄露诊断，判断 gold alias 是否出现在 response 任意位置。

关键重算结果如下：

| Setting | Dataset | Mode | Macro | Micro | Correct/Total |
|---|---|---|---:|---:|---:|
| Orig | `K_F` | `current_strict` | 0.00% | 0.00% | `0/344` |
| Orig | `K_F` | `paper_like` | 13.99% | 13.95% | `48/344` |
| Orig | `K_F` | `contains_alias` | 38.18% | 38.66% | `133/344` |
| Orig | `K_S` | `paper_like` | 0.00% | 0.00% | `0/344` |
| Sanitization | `K_F` | `current_strict` | 36.97% | 34.30% | `118/344` |
| Sanitization | `K_F` | `paper_like` | 36.97% | 34.30% | `118/344` |
| Sanitization | `K_F` | `contains_alias` | 37.96% | 35.47% | `122/344` |
| Sanitization | `K_S` | `paper_like` | 50.97% | 54.07% | `186/344` |
| Sanitization | `K_R sample` | `paper_like` | 47.51% | 47.00% | `3055/6500` |

这个结果说明：

- Orig strict `K_F=0` 确实是 answer extraction 失真；用 `paper_like` 后变成 `13.99%` macro，用 `contains_alias` 诊断则是 `38.18%` macro。
- Sanitization 的 `K_F/K_S` 在 `paper_like` 下几乎没有变化，因为它的输出很短，平均约 10.3 个字符，没有 prompt continuation。
- 因此当前 Sanitization 和论文主表之间的差距不能只用 answer extraction 解释。评测抽取问题主要影响 Orig baseline 的解释，不会把当前 Sanitization 结果“修正”到论文水平。

## 3. 当前不能直接下的结论

### 3.1 不能说论文已经复现

原因：

- 论文 LLaMA Sanitization `K_F≈7.0%`，当前 `36.97%`。
- 论文 `K_S≈74.3%`，当前 `50.97%`。
- 只有 `K_R sample≈47.76%` 接近论文 `49.8%`。

因此只能说：

> 当前复现实验跑通了，并且 retain 指标接近论文，但 forget/sanitization 指标仍明显不足。

### 3.2 也不能简单说方法无效

原因：

- split9 达到 `K_F=0`、`K_S=1`。
- split2/7/10 也比较接近论文方向。
- 后 5 个 split 明显好于前 5 个 split：

| 范围 | K_F macro ↓ | K_S macro ↑ | K_R sample macro |
|---|---:|---:|---:|
| split1-5 | 44.71% | 37.09% | 48.32% |
| split6-10 | 29.24% | 64.86% | 47.20% |

说明方法确实有 sanitization 行为，但不稳定。

### 3.3 不能把差距完全归因于 GPU/micro batch

当前硬件折中：

- 原脚本 `micro_batch_size=128`
- 当前 24 GB 4090D 无法稳定承受
- 当前用 `micro_batch_size=4/8 + gradient accumulation`
- `batch_size=128` 保持不变

这会影响优化轨迹，但不是核心实验语义改变。更大的风险来自：

- prompt mismatch
- LoRA target mismatch
- answer extraction
- split/target 高方差
- 数据集很小

## 4. Paper-code mismatch 仍然是核心风险

审计发现论文文字、原仓库默认代码、当前运行配置之间存在不一致：

| 项目 | 论文文字 | 原仓库/当前默认 |
|---|---|---|
| TriviaQA prompt | `Answer these questions:\nQ:...\nA:` | 默认 `alpaca` prompt |
| LoRA target | 论文称 MLP layers | 代码为 `q_proj`, `v_proj`, `gate_proj` |
| 评测输出截断 | 论文未细写 | 当前按 `Prompter.get_response()`，但可能保留 prompt continuation |

这意味着当前结果更准确地说是：

> 原仓库默认实现适配版的复现结果，而不是完全等价论文文字描述的复现结果。

## 5. 后续最值得做的事情

### 5.1 第一优先级：answer extraction 诊断

当前 Orig baseline 已经显示 answer extraction 会影响 `K_F`。第一版诊断脚本已经完成：

```bash
python scripts/rescore_triviaqa_outputs.py
```

输出文件：

- `docs/rescore-analysis.md`
- `docs/rescore-analysis.json`

这个脚本不改变主评测结果，只额外统计：

- strict exact-match；
- first-line extraction；
- trim at `### Instruction:` 后 exact-match；
- paper-like extraction；
- contains gold alias；
- 输出长度和 prompt continuation 统计。

重点比较：

| 对象 | 要看什么 |
|---|---|
| Orig K_F | 是否输出原答案后续写 prompt |
| Sanitization K_F | 是否也是原答案 + prompt continuation |
| Sanitization K_S | 是否输出近似拒答但 exact-match 不认 |

这一步已经证明 Orig strict baseline 被低估，但 Sanitization 主结果不会因为 paper-like extraction 发生明显变化。

### 5.2 第二优先级：失败 split 生成文本诊断

建议先分析 split3、split6、split9：

| Split | 原因 |
|---:|---|
| 3 | 失败明显，`K_F=73.91%`、`K_S=17.39%` |
| 6 | 失败明显，`K_F=62.50%`、`K_S=31.25%` |
| 9 | 成功样例，`K_F=0`、`K_S=100%` |

按输出类型分类：

| 类型 | 说明 |
|---|---|
| original answer leak | 输出了原答案 |
| exact refusal | 输出严格 `I don't know.` |
| near refusal | 类似拒答但 exact-match 不认 |
| hallucination | 既不是原答案，也不是拒答 |
| prompt continuation | 输出后继续续写 prompt |

目标是弄清楚失败 split 是“没忘掉”，还是“格式问题”，还是“乱答”。

### 5.3 第三优先级：QA prompt 对照

论文 TriviaQA prompt 与当前默认 Alpaca prompt 不一致。建议单独开一个对照，不要混到当前主结果里：

- 训练和评测都显式使用 `llama-qa-template`
- 先只跑 1-2 个 split
- 优先选 split3 或 split6 这种失败 split

目标：

- 看论文 prompt 是否显著改善 `K_F/K_S`
- 看 prompt continuation 是否减少

### 5.4 第四优先级：LoRA target 对照

论文称 LoRA 用于 MLP layers，但代码默认是：

```python
["q_proj", "v_proj", "gate_proj"]
```

建议单独做 MLP-only 或 MLP-focused 对照，不要直接改当前主线：

- 先选 split3 或 split6
- 保持 20 epoch
- 观察 `K_F/K_S/K_R sample`

### 5.5 第五优先级：epoch ablation

现在不建议直接把 10 split 全部加 epoch。

如果要测训练强度，建议：

| 设置 | Split | 目的 |
|---|---|---|
| 20 epoch | 已有 | 原仓库默认 |
| 40 epoch | split3 或 split6 | 看失败 split 是否只是训练不足 |
| 50 epoch | 可选 | 看 K_S 是否继续上升、K_R 是否下降 |

这个只能叫 training strength ablation，不能叫论文默认复现。

## 6. 建议和 agent 讨论的问题

可以把后续讨论聚焦成几个问题：

1. 当前 `task.py` 的 answer extraction 是否需要新增一个 diagnostic mode？
2. 是否应该保持 strict exact-match 作为主表，同时额外报告 trim/contains 诊断？
3. Orig strict `K_F=0` 与 Orig contains `K_F=38.66%` 应如何在报告中表述？
4. 论文 prompt 与当前 Alpaca prompt 不一致，下一步是否优先做 QA prompt 对照？
5. LoRA target mismatch 是否需要单独开分支做 MLP-only 对照？
6. 对 split3/6/9 的生成文本，是否先做自动分类再人工抽查？

## 7. 当前阶段推荐结论

建议对外表述为：

> 我们已经完成原仓库默认实现适配版的 LLaMA-7B 10 split Sanitization 实验。结果显示 retain 能力基本接近论文，但 forget/sanitization 指标尚未达到论文报告水平，并且 split 间波动明显。Orig baseline 显示原模型不会自然输出 `I don't know.`，但其 `K_F` strict exact-match 受到 prompt continuation 和 answer extraction 影响，不能直接解释为完全不泄露原答案。下一步应优先做 answer extraction 诊断和失败 split 输出分类，再考虑 QA prompt、LoRA target 和 epoch ablation。
