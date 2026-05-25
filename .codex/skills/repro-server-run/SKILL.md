---
name: repro-server-run
description: Use when planning or instructing runs for this repository. Prioritize minimal-change reproduction of the original paper on a Linux GPU server, prefer HF-format LLaMA 7B, and provide conservative single-GPU run settings before scaling up.
---

# Reproduction Server Run

目标:
- 优先最小改动复现原论文
- 优先沿用原仓库的 LLaMA 专用代码路径
- 不优先改成 AutoModel 多模型框架

## 模型原则

1. 主路线:
- HF-format LLaMA 7B
- 服务器模型目录默认:
  - `/root/autodl-tmp/models/llama-hf/7B`

2. 不优先:
- Qwen
- TinyLlama 作为主复现模型
- GPT-J 支线改造

3. TinyLlama 只用于 smoke test 时才提及。

## 运行环境原则

1. 原论文是 A6000 级别显卡。
2. 当前若使用 1x4090D 24GB:
- 先跑保守 smoke test
- 再逐步加大

## 默认服务器运行顺序

先让用户执行:

```bash
cd /root/autodl-tmp/projects/knowledge-sanitization
git pull --rebase origin master
conda activate ks310
```

若是首轮验证, 默认建议:

```bash
LOAD_IN_8BIT=false BATCH_SIZE=8 MICRO_BATCH_SIZE=1 NUM_EPOCHS=1 bash run_sanitization.sh
```

## 放大原则

1. 首先确认:
- 模型能加载
- 训练能产出 `adapter_config.json`
- 评测能正常写结果

2. 只有 smoke test 通过后, 才建议增大:
- `BATCH_SIZE`
- `MICRO_BATCH_SIZE`
- `NUM_EPOCHS`

3. 没有充分证据前, 不要直接建议回到原论文那种大 batch。

## 结果路径

训练输出默认看:

```text
/root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization
```

评测结果默认看:

```text
/root/autodl-tmp/outputs/triviaqa_1/results/trivia_qa
```

## 常见报错处理原则

1. 若训练失败:
- 先修训练
- 不继续评测

2. 若缺 `adapter_config.json`:
- 通常是训练没成功
- 不要把它误判成评测脚本主问题

3. 若 8-bit 报错:
- 优先检查布尔参数是否真的关闭
- 再看 `transformers`, `accelerate`, `peft`, `bitsandbytes` 的组合
