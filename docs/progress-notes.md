# Knowledge Sanitization 复现阶段简要汇总

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

当前只完成了 `triviaqa_1` 单 split 的一轮 LoRA 结果：

| 指标 | 当前结果 | 解释 |
|---|---:|---|
| `K_F` | 43.48% | 仍有较多目标知识被答出 |
| `K_S` | 8.70% | 几乎没有学会稳定输出拒答短语 |
| `K_R` | 48.77% | retain 能力接近论文水平 |

与论文 LLaMA-7B Sanitization 对比：

| 指标 | 论文结果 | 当前结果 | 判断 |
|---|---:|---:|---|
| `K_F` | 约 7.0% | 43.48% | 遗忘效果不足 |
| `K_S` | 约 74.3% | 8.70% | sanitization 行为未学出来 |
| `K_R` | 约 49.8% | 48.77% | 接近论文 |

# 只跑了split 1 原文可能是10个split取平均

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

---

## 6. 当前差距的可能原因

当前 `K_R` 接近论文，但 `K_F / K_S` 明显较差，说明主要问题不是 retain 崩坏，而是 sanitization 学习不足。

可能原因：

1. 训练强度不足。
2. `K_S` 样本比例低，拒答信号被 `K_R` 稀释。
3. exact match 对 `I don’t know.` 过严。
4. 训练数据是否确实为 `K_S + K_R` 仍需核查。
5. 评测时 LoRA adapter 是否正确加载仍需确认。
6. 当前只跑了 `triviaqa_1`，不能直接等同于论文 10 split 平均结果。

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
2. 当前只完成 `triviaqa_1` 单 split 的一轮 LoRA 结果。
3. `K_R` 接近论文，但 `K_F / K_S` 与论文差距较大。
4. 当前不能认为论文效果已复现。
5. 最大工程瓶颈是 full `K_R` 评测成本过高。
6. 下一步应优先补 10 split 的 `K_F / K_S`、Orig 小集合对照和生成文本分析。
7. 调参阶段应使用 `K_R` 抽样评测，最终少数配置再跑 full `K_R`。