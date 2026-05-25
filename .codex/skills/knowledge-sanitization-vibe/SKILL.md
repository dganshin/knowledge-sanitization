---
name: knowledge-sanitization-vibe
description: Use when working in this repository. Covers the long-lived collaboration context for local code editing plus remote Linux execution, minimal-change paper reproduction, default server paths, result locations, anti-disconnect reminders, and safe single-4090D tuning guidance.
---

# Knowledge Sanitization Vibe

这个 skill 是本仓库的总入口。处理本仓库任务时, 优先按这里的约束走。

## 默认协作模式

1. 代码在本地 MacOS 或 Windows 修改。
2. 训练和评测只在远端 Linux 服务器执行。
3. 本地不伪装成已经完成服务器验证。
4. 改完代码后:
- 提交
- 推送到用户 fork
- 明确提醒服务器 `git pull --rebase origin master`

## 当前主目标

1. 优先最小改动复现原论文。
2. 优先 HF-format LLaMA 7B。
3. 不优先多模型泛化改造。
4. 不轻易改:
- 主训练流程
- prompt 逻辑
- 评测指标
- LoRA target modules

## 什么时候读额外参考

1. 若要告诉用户服务器怎么跑:
- 读 `references/server-runbook.md`

2. 若要告诉用户结果去哪里看:
- 读 `references/result-reading.md`

3. 若要讨论单卡 4090D 怎么提负载:
- 读 `references/tuning.md`

## 默认运行原则

1. 首轮先 smoke test。
2. 先确认:
- 训练成功
- 生成 `adapter_config.json`
- 评测结果落盘
3. 之后再逐步放大 `MICRO_BATCH_SIZE` 和 `BATCH_SIZE`。

## 长任务提醒

在给任何长时间服务器命令前, 先提醒:

```bash
tmux new -s ks_run
```

如果用户不用 `tmux`, 再给:

```bash
screen -S ks_run
```

## 当前关键路径

- 项目目录:
  - `/root/autodl-tmp/projects/knowledge-sanitization`
- 模型目录:
  - `/root/autodl-tmp/models/llama-hf/7B`
- checkpoint 目录:
  - `/root/autodl-tmp/checkpoints`
- 输出目录:
  - `/root/autodl-tmp/outputs`
