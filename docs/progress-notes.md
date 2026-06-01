# Knowledge Sanitization 复现阶段简要汇总

实验原始记录请持续追加到 [`docs/experiment-log.md`](./experiment-log.md)。本文件保留阶段性总结，不作为逐次实验流水账。

## 1. 当前目标

当前阶段目标是尽量最小改动复现论文 **Knowledge Sanitization of Large Language Models** 在 **LLaMA-7B** 上的训练与评测流程。

核心指标：

| 指标 | 含义 | 方向 |
|---|---|---|
| `K_F` | forget 问题是否仍输出原答案 | 越低越好 |
| `K_S` | forget 问题是否输出 `I don’t know.` | 越高越好 |
| `K_R` | retain 问题是否保持正确回答 | 接近 Orig 越好 |

---

## 2. 当前工程状态

已确认原仓库期望的是 **HuggingFace Transformers 格式的 LLaMA-7B**，不是 Meta 原始 checkpoint。

当前模型路径：

`/root/autodl-tmp/models/llama-hf/7B`

已跑通：

- LLaMA-7B 加载
- tokenizer 加载
- LoRA 训练
- adapter 保存与加载
- `K_F / K_S / K_R` 三类评测
- 结果导出



---

## 3. 当前已有结果

当前主要结果已补齐 `triviaqa_1` 到 `triviaqa_10` 十个 split。split1-5 使用 `micro_batch_size=8`，split6-10 因 24 GB GPU 上 `micro_batch_size=8` 训练 OOM，改用 `micro_batch_size=4`，但 `batch_size=128` 保持不变。

| 指标 | 当前结果 | 解释 |
|---|---:|---|
| `K_F` macro | 36.97% | forget 侧仍有原答案被答出，但后 5 个 split 明显改善 |
| `K_S` macro | 50.97% | sanitization phrase 有明显学习，但仍低于论文 |
| `K_R` sample macro | 47.76% | retain 能力基本接近论文水平 |

split1-10 明细：

| Split | K_F ↓ | K_S ↑ | K_R sample → | K_R sample size |
|---:|---:|---:|---:|---:|
| 1 | 39.13% | 13.04% | 45.60% | 2000 |
| 2 | 15.09% | 69.81% | 52.00% | 500 |
| 3 | 73.91% | 17.39% | 49.40% | 500 |
| 4 | 57.89% | 28.95% | 49.00% | 500 |
| 5 | 37.50% | 56.25% | 45.60% | 500 |
| 6 | 62.50% | 31.25% | 48.40% | 500 |
| 7 | 20.69% | 68.97% | 40.80% | 500 |
| 8 | 32.26% | 54.84% | 45.40% | 500 |
| 9 | 0.00% | 100.00% | 50.60% | 500 |
| 10 | 30.77% | 69.23% | 50.80% | 500 |

与论文 LLaMA-7B Sanitization 对比：

| 指标 | 论文结果 | 当前结果 | 判断 |
|---|---:|---:|---|
| `K_F` | 约 7.0% | 36.97% macro | 遗忘效果仍明显不足 |
| `K_S` | 约 74.3% | 50.97% macro | sanitization 行为有一定学习，但仍不足 |
| `K_R` | 约 49.8% | 47.76% sample macro | 接近论文，但当前为 sample 评测 |

说明：当前 `K_F/K_S` 已覆盖 10 个 split full eval；`K_R` 不是 full eval，而是 sample eval，其中 split1 为 2000 条，split2-10 为 500 条。

---

## 4. 数据集规模现象

10 个 split 的测试集规模高度不对称：

| 集合 | 规模特点 | 作用 |
|---|---|---|
| `K_F` | 每个 split 约 23–58 条 | 测目标知识是否仍被答出 |
| `K_S` | 与 `K_F` 同规模 | 测是否输出 `I don’t know.` |
| `K_R` | 每个 split 约 17900 条 | 测大量非目标知识是否保持 |

这不是 bug，而是论文协议本身设计：

- `K_F / K_S` 只围绕少量 forgetting targets；
- `K_R` 覆盖大规模 retain questions；
- 训练文件约 533 条，其中约 80 条为 `K_S`，约 453 条为 `K_R`，符合约 `15:85` 的比例。

---

## 5. 当前主要问题

### 5.1 不是 GPU 问题

已确认评测阶段实际运行在 GPU 上：

- `Model param device: cuda:0`
- `Eval device: cuda:0`
- 显存占用约 20GB+
- GPU 利用率约 96%

### 5.2 主要瓶颈是 `K_R` 全量评测成本

当前 `K_R` 全量评测非常昂贵：

- LLaMA-7B
- beam search，`beam=4`
- `max_new_tokens=256`
- generative exact-match
- 每个 split 约 17900 条

当前观察到一个 split 的 full `K_R` 评测约需数小时。若 10 个 split 全量跑 Orig + LoRA，成本过高。

### 5.3 Orig baseline 的 answer extraction 问题

已完成 Orig baseline 的 `K_F/K_S` full eval，严格 exact-match 结果均为 `0.0`。但抽查生成文本发现，原模型经常先输出正确原答案，然后继续续写 `### Instruction:` prompt，例如 `Paris\n\n### Instruction:...`。当前评测会把整段 response 与 gold alias 做 exact-match，因此这类输出被判错。

诊断统计：

| Orig 诊断口径 | K_F | K_S |
|---|---:|---:|
| 当前严格 exact-match | 0.00% | 0.00% |
| response 包含 gold alias | 38.66% | 0.00% |
| 截断到下一个 `### Instruction:` 后 exact-match | 13.95% | 0.00% |

结论：Orig 不会自然输出 `I don't know.`，但 Orig `K_F=0` 不能单独解释为原模型完全不会泄露答案；这里存在 prompt continuation / answer extraction 问题。

---

## 6. 当前差距的可能原因

当前 `K_R` sample 接近论文，但 `K_F / K_S` 明显较差，说明主要问题不是 retain 崩坏，而是 sanitization 学习不足。

可能原因：

1. 训练强度不足。
2. `K_S` 样本比例低，拒答信号被 `K_R` 稀释。
3. exact match 对 `I don’t know.` 过严。
4. 训练数据是否确实为 `K_S + K_R` 仍需核查。
5. 评测时 LoRA adapter 是否正确加载仍需确认。
6. 当前只跑了 `triviaqa_1` 到 `triviaqa_5`，不能直接等同于论文 10 split 平均结果。

---

## 7. 下一步建议

### 7.1 先跑低成本关键评测

不要继续直接跑 full `K_R`。

优先补：

- 10 个 split 的 LoRA `K_F / K_S`
- 10 个 split 的 Orig `K_F / K_S`
- `K_R` 只做 sample 评测，例如 sample 1000，固定 seed

### 7.2 导出生成文本

导出 `triviaqa_1` 的全部 test-forget 生成结果，检查：

- 是否仍输出原答案；
- 是否输出 `I don’t know.`；
- 是否输出近似拒答；
- 是否因格式问题导致 exact match 失败；
- 是否输出幻觉答案。

### 7.3 后续训练

在不改变论文主逻辑的前提下增强训练强度，例如：

`LOAD_IN_8BIT=false BATCH_SIZE=16 MICRO_BATCH_SIZE=2 NUM_EPOCHS=3 bash run_sanitization.sh`

训练后先看：

| 指标 | 期望 |
|---|---|
| `K_F` | 明显下降 |
| `K_S` | 明显上升 |
| `K_R_sample` | 接近 Orig 或接近当前 49% |

如果 `K_F` 不降、`K_S` 不升，不应继续跑 full `K_R`。

---

## 8. 当前阶段结论

1. LLaMA-7B 训练与评测链路已跑通。
2. 当前完成 `triviaqa_1` 到 `triviaqa_10` 的 LoRA 训练与 `K_F / K_S / K_R sample` 评测。
3. `K_R sample` 接近论文，但 `K_F / K_S` 与论文仍有差距。
4. 当前不能认为论文效果已复现。
5. 最大工程瓶颈是 full `K_R` 评测成本过高。
6. 下一步应优先做 answer extraction 诊断、prompt/LoRA target ablation 和生成文本分析。
7. 调参阶段应使用 `K_R` 抽样评测，最终少数配置再跑 full `K_R`。
