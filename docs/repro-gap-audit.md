# 复现差异审计

审计日期：`2026-05-31`

审计范围：

- 论文：Knowledge Sanitization of Large Language Models，arXiv `2309.11852`
- 原仓库基准 commit：`7214e4db1fc6dfbab4a66a087fc3965881d1fe68`
- 当前分支：`paper-repro`
- 当前 HEAD：`532e4c913d840048cc06ab4ac07523dd226cec72`
- 当前主要实验 run：`test_mb8_eval4_split1`

本审计只做静态代码、日志和数据检查；未运行训练，也未运行新的大规模评测。

## 1. 当前 Git 状态

| 项目 | 结果 |
|---|---|
| 当前分支 | `paper-repro` |
| 当前 HEAD | `532e4c913d840048cc06ab4ac07523dd226cec72` |
| `origin` | `https://github.com/dganshin/knowledge-sanitization.git` |
| `upstream` | `https://github.com/yoichi1484/knowledge-sanitization.git` |
| 原始 commit | 本地可访问 `7214e4db1fc6dfbab4a66a087fc3965881d1fe68` |

近 10 个 commit 显示当前分支主要包含三类变更：运行脚本修复、实验日志/输出记录、`task.py` 评测加速与抽样支持。

## 2. 论文、原仓库、当前分支的关键差异

| 项目 | 论文描述 | 原仓库 `7214e4d` | 当前 `paper-repro` | 一致性 | 风险 |
|---|---|---|---|---|---|
| 模型 | LLaMA 7B 与 GPT-J 6B；表 2 报 LLaMA 7B Sanitization | 脚本占位 `{your-llama-path}/llama-hf/7B` | `/root/autodl-tmp/models/llama-hf/7B` | 基本一致 | 低 |
| 任务 | TriviaQA closed-book QA | TriviaQA 数据目录已提供 | 使用同一 `data/triviaqa_1..10` | 一致 | 低 |
| TriviaQA prompt | 论文脚注给出 `Answer these questions:\nQ: ____\nA:` | `finetune.py` 默认 `alpaca`；`task.py` 默认空模板，`Prompter` fallback 到 `alpaca`；仓库另有 `llama-qa-template.json` 但脚本未使用 | 仍默认 `alpaca`，脚本未显式传 `--prompt_template` | 论文 vs 代码不一致 | 高 |
| LoRA target | 论文称应用到 MLP layers，rank `r=8` | 默认 `q_proj`, `v_proj`, `gate_proj` | 仍为 `q_proj`, `v_proj`, `gate_proj` | 论文 vs 代码不一致；当前未额外改变 | 高 |
| Sanitization data | `K_S ∪ K_R` | `train_5-forget-answers_85-percent-retain.json` | `.jsonl`，实际内容为 JSON array，可被 HF JSON loader 读取 | 语义一致 | 低 |
| Sanitization phrase | `I don't know.` | 训练样本中使用 `I don't know.` | 相同 | 一致 | 低 |
| Epoch | 表述为 fine-tuning；脚本用 20 epoch | `run_sanitization.sh` 传 `--num_epochs 20` | 仍传 `--num_epochs 20` | 一致 | 低 |
| Effective batch | 未在论文表格充分展开；原脚本为 `batch_size=128, micro_batch_size=128` | `gradient_accumulation_steps = batch_size // micro_batch_size`，原脚本等于 1 | 多 split 脚本为 `batch_size=128, micro_batch_size=8`，gradient accumulation 等于 16 | effective batch 保持 128，但优化数值轨迹不同 | 中 |
| 8-bit loading | 论文未强调；原代码固定 `load_in_8bit=True` | 固定 8-bit | 支持参数化，当前脚本传 `--load_in_8bit=false` | 工程适配，精度/显存不同 | 中 |
| 评测 beam | 论文 beam size 4 | `--num_beams=4` | `--num_beams=4` | 一致 | 低 |
| K_F/K_S 评测 | 论文报平均 accuracy | 原脚本 full eval 并 `--show` | 多 split 脚本 full eval，不 `--show` | 语义基本一致 | 低 |
| K_R 评测 | 论文表为 retention accuracy | 原脚本 full K_R | 多 split 脚本使用 sample：split1=2000，其他 split=500 | 当前结果不是 full K_R | 中 |
| 评测实现 | 论文未给实现细节 | `pipeline("text-generation")` 逐条生成 | batched `model.generate`，支持 `eval_batch_size` | 可能有极小生成差异，但参数保留 | 中 |
| split/run 数量 | 论文表 2 写明结果为 five independent experiment runs 的平均 | 仓库提供 `triviaqa_1` 到 `triviaqa_10` | 当前已跑 split1-5，后续可继续 split6-10 | 论文与数据目录命名不完全同一层概念 | 中 |
| `test_size` | 无 | 循环中达到 N 后停止，相当于前 N 条 | 支持 `--sample_seed` 后 shuffle，再 select N 条 | 当前 sample 可复现，但不是原仓库默认行为 | 中 |

## 3. 改动分类

### 3.1 必要工程适配

| 文件 | 改动 | 原行为 | 当前行为 | 影响 |
|---|---|---|---|---|
| `run_sanitization.sh` | 模型路径改为 AutoDL 路径 | 占位路径不可直接运行 | 指向 `/root/autodl-tmp/models/llama-hf/7B` | 必要 |
| `run_sanitization.sh` | 训练数据扩展名 `.json` 改为 `.jsonl` | 原路径在当前仓库不存在 | 当前数据文件存在 | 必要 |
| `finetune.py` | `load_in_8bit` 参数化 | 固定 8-bit | 可传 `--load_in_8bit=false` | 为解决当前环境报错 |
| `task.py` | 增加 `eval_batch_size` | 逐条 pipeline 生成 | batched generate | 提速，不应改变指标定义 |
| `task.py` | 增加 `sample_seed` | 只支持顺序截断 | 支持随机可复现抽样 | 用于低成本 K_R |
| `run_sanitization_10splits.sh` | 增加 run log、summary、RUN_ID | 原脚本只跑单 split | 可追踪多 split | 实验管理 |

### 3.2 会影响优化动态的硬件折中

| 项目 | 原仓库 | 当前实验 | 判断 |
|---|---|---|---|
| `micro_batch_size` | `128` | `8`，早期单跑为 `4` | 显存折中；effective batch 仍保持 `128` |
| `gradient_accumulation_steps` | `1` | `16` 或 `32` | optimizer step 数大体接近，但数值轨迹会变 |
| `load_in_8bit` | `true` | `false` | 显存更高、量化误差更少；不应简单认为更差 |
| GPU 显存 | 论文使用 RTX A6000 | 当前远端为 4090D 24 GB | A6000 官方规格为 48 GB GDDR6 ECC；24 GB 上 OOM 合理 |

`micro_batch_size` 无法开到 128 本身不应被视为核心方法改变。只要 `batch_size=128` 保持不变，当前做法是在 24 GB 单卡上用 gradient accumulation 近似原 effective batch。它会带来数值差异，但通常不足以单独解释 `K_S` 从论文约 `0.743` 降到当前 split1-5 macro `0.3709`。

### 3.3 明显可能影响论文级复现的语义差异

| 风险点 | 证据 | 影响 |
|---|---|---|
| Prompt mismatch | 论文 TriviaQA prompt 是 `Answer these questions:\nQ:...\nA:`；原脚本和当前脚本都没有显式传 `llama-qa-template`，默认落到 `alpaca` | 高。训练和评测 prompt 可能与论文文字不一致 |
| LoRA target mismatch | 论文写 MLP layers；代码使用 `q_proj`, `v_proj`, `gate_proj` | 高。方法实现与论文文字存在不一致 |
| K_R 当前为 sample | 当前 run 的 K_R 为 split1=2000、split2-5=500 | 中。可用于趋势判断，不等价论文 full retention |
| 评测实现从 pipeline 改为 batched generate | 参数保留，但 padding、batch decode 与 pipeline 细节不同 | 中低。可能造成个别答案差异，不是主要风险 |

## 4. 评测语义审计

| 项目 | 原仓库 `7214e4d` | 当前 `paper-repro` | 判断 |
|---|---|---|---|
| 数据加载 | `load_from_disk(args.path_dataset)` | 相同 | 一致 |
| LoRA 判断 | `PeftModel.from_pretrained` 后逐条生成 | 相同加载路径，日志打印 `LoRA: Active` | 一致 |
| `--test_size` | 循环中达到 N 后 `break`，等价于前 N 条 | 若 `sample_seed>=0` 先 shuffle，再 select N 条 | 当前支持随机 sample；默认 `-1` full eval 不变 |
| `--eval_batch_size` | 无，逐条 pipeline | batched generate | 只影响吞吐和显存，指标定义不变 |
| `num_beams` | 传给 `GenerationConfig` | 相同 | 一致 |
| `top_k` | 传给 `GenerationConfig` | 相同 | 一致 |
| `max_new_tokens` 参数名 | 实际传给 pipeline 的 `max_length` | 仍传给 `model.generate(max_length=...)` | 保留原仓库语义，但变量名本身并非严格的 `max_new_tokens` |
| exact match | `predicted_answer in task_output`，大小写和末尾句点容忍 | 相同函数 | 一致 |
| K_S gold | `["i don't know.", "I don't know."]` | 相同数据 | 一致 |

当前 split1-5 的 K_S 低，不主要是 exact match 过严造成的。抽查 `K_S` 结果显示，大量错误输出是原答案或其他实体，例如 split1 中常见输出包括 `Paris`、`Finland`、`Cheese`，split3 中常见输出包括 `Gin`、`Afghanistan`。这说明模型确实没有稳定输出 sanitization phrase。

## 5. 当前训练和评测是否真实发生

日志证据来自 `docs/experiment-command-logs/test_mb8_eval4_split1/`。

| 证据 | 观察 |
|---|---|
| 训练样本 mapping | 每个 split 训练日志均显示处理 `533` 条训练样本 |
| 可训练参数 | 每个 split 日志显示 `trainable params: 8060928`，约 `0.1195%` |
| loss 下降 | split1 从约 `3.1151` 降到 `0.5976`；其他 split 类似 |
| train summary | split1 `train_loss=1.6113`，split2-5 在 `1.59-1.60` 附近 |
| LoRA 加载 | K_F/K_S/K_R eval 日志均出现 `LoRA: Active` |
| eval device | eval 日志显示 `Eval device: cuda:0, batch_size: 4` |

结论：

- 当前训练确实发生，不是空跑。
- 当前评测确实加载了 LoRA adapter。
- 当前低 `K_S` 不是因为“根本没训练”或“评测没有加载 LoRA”。
- 更合理的解释是：prompt/LoRA target 的 paper-code mismatch、split 高方差、硬件折中和随机性共同影响了 sanitization 行为。

## 6. 当前 split1-5 结果解释

| Split | K_F ↓ | K_S ↑ | K_R sample → | K_R sample size |
|---:|---:|---:|---:|---:|
| 1 | `0.391304347826087` | `0.13043478260869565` | `0.456` | `2000` |
| 2 | `0.1509433962264151` | `0.6981132075471698` | `0.52` | `500` |
| 3 | `0.7391304347826086` | `0.17391304347826086` | `0.494` | `500` |
| 4 | `0.5789473684210527` | `0.2894736842105263` | `0.49` | `500` |
| 5 | `0.375` | `0.5625` | `0.456` | `500` |

| 汇总方式 | K_F ↓ | K_S ↑ | K_R → |
|---|---:|---:|---:|
| Macro average | `0.4470651094512327` | `0.3708869435689305` | `0.4832` |
| Micro average | `0.40236686390532544` | `0.4319526627218935` | `0.473` |

论文表 2 中 LLaMA Sanitization 的 TriviaQA 指标为 `Forget=7.0%`、`Retain=49.8%`。当前 `K_R` sample macro `0.4832` 接近论文 retain，但 `K_F` 仍显著偏高，`K_S` 也显著低于论文期望的拒答行为。

这说明：

- retain 评测链路和模型基本能力没有明显崩坏；
- sanitization 行为没有稳定复现，尤其 split3/4 仍大量输出原答案；
- 不能把当前结果称为“已完全复现论文”；
- 更准确的表述是：当前分支在必要工程适配后跑通了实验链路，retain 指标接近论文，但 forget/sanitization 指标未达到论文报告水平。

## 7. 是否继续跑 split6-10

建议继续跑，但目标应是“补齐趋势证据”，不是期待单靠增加 split 自动修复问题。

原因：

- K_F/K_S 每个 split 样本数很小，split 间波动大；补齐 10 split 可以降低统计偶然性。
- 当前前 5 split 已经显示明显不稳定：split2 接近论文方向，split3 明显失败。
- 若 10 split macro 仍明显偏离论文，应优先做 prompt/LoRA target ablation，而不是继续重复相同配置。

## 8. 后续建议

优先级从高到低：

1. 保留当前 `paper-repro` 作为“原仓库可运行适配 + 结果记录”分支，继续补齐 split6-10。
2. 单独开实验分支测试论文 prompt：训练和评测同时显式传 `--prompt_template llama-qa-template`。
3. 单独开实验分支测试论文文字中的 MLP-only LoRA target，而不是在当前结果分支直接混改。
4. 如果资源允许，跑 Orig baseline，确认 base model 在当前评测链路上的 K_F/K_R 是否接近论文 `Orig.`。
5. GPT-J 可作为补充，但当前最重要问题仍是 LLaMA prompt/LoRA target 与论文文字不一致。

## 9. 外部来源

- arXiv: `https://arxiv.org/abs/2309.11852`
- OpenReview PDF mirror: `https://openreview.net/pdf?id=RD10QWcDAv`
- NVIDIA RTX A6000 spec: `https://www.nvidia.com/en-us/products/workstations/rtx-a6000/`
