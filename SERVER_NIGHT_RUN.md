# Server Night Run

## 当前原则

1. 不继续改训练/评测主逻辑来追求方便。
2. 方便性都放在脚本层。
3. 过夜长实验前, 先做一轮稳定性测试。

## 关键结论

### 自动关机逻辑

- `run_orig_baseline.sh` 不会关机。
- `run_sanitization_nightly.sh` 只有在:
  - `SHUTDOWN_ON_SUCCESS=true`
  - 且整条脚本成功跑完

  才会执行 `poweroff`。

- 如果中途报错, 因为脚本用了 `set -euo pipefail`, 会直接退出, 不会继续往下走到关机。

### 推荐顺序

不要手动记两条命令顺序, 直接用:

```bash
tmux new -s ks_run
cd /root/autodl-tmp/projects/knowledge-sanitization
git fetch origin
git rebase origin/master
zsh /root/start_mihomo.sh
bash run_full_nightly.sh
```

如果你明确是过夜实验, 再加:

```bash
GPU_TIER=24g SHUTDOWN_ON_SUCCESS=true bash run_full_nightly.sh
```

## 先压测, 再过夜

### 第一步: 稳定性测试

先不要自动关机, 也不要直接过夜。

推荐先跑:

```bash
tmux new -s ks_run
cd /root/autodl-tmp/projects/knowledge-sanitization
git fetch origin
git rebase origin/master
zsh /root/start_mihomo.sh
GPU_TIER=24g SHUTDOWN_ON_SUCCESS=false bash run_full_nightly.sh
```

同时另开一个窗口看:

```bash
watch -n 1 nvidia-smi
```

观察:
- 显存占用
- GPU-Util
- 功耗
- 是否 OOM
- 是否中途报错

### 第二步: 确认稳定后再过夜

确认这一轮没炸, 才跑:

```bash
GPU_TIER=24g SHUTDOWN_ON_SUCCESS=true bash run_full_nightly.sh
```

## 24G 档位的当前默认值

由 `run_sanitization_nightly.sh` 控制:

```text
BATCH_SIZE=16
MICRO_BATCH_SIZE=2
NUM_EPOCHS=3
PREPROCESS_NUM_PROC=8
DATALOADER_NUM_WORKERS=8
EVAL_BATCH_SIZE=4
LOAD_IN_8BIT=false
```

注意:
- 训练 batch 和评测 batch 不是一回事。
- `MICRO_BATCH_SIZE` 主要决定训练显存。
- `EVAL_BATCH_SIZE` 主要决定评测显存, 对 `7B + beam=4 + max_new_tokens=256` 很敏感。
- 24G 卡先从 `EVAL_BATCH_SIZE=4` 起步, 稳了再手动试 `6` 或 `8`。

如果稳定性测试显示卡还很空, 再考虑上调。

## 文本结果

脚本会把轻量文本结果导到仓库:

```text
analysis_exports/triviaqa_1/
analysis_exports/triviaqa_1_orig/
```

这样第二天你无需在显卡实例里提交 git, 但以后需要时可以再手动提交这些纯文本结果。
