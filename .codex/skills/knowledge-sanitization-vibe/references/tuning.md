# Single 4090D Tuning

目标:
- 先跑通
- 再把单卡 4090D 利用率拉高一点
- 不为了省显存过早强依赖 8-bit

## 优先级

1. 先调 `MICRO_BATCH_SIZE`
2. 再调 `BATCH_SIZE`
3. 最后再考虑更激进配置

原因:
- `MICRO_BATCH_SIZE` 更直接影响单步显存占用
- `BATCH_SIZE` 更多影响梯度累积

## 建议顺序

### 最保守

```bash
LOAD_IN_8BIT=false BATCH_SIZE=8 MICRO_BATCH_SIZE=1 NUM_EPOCHS=1 bash run_sanitization.sh
```

### 轻度放大

```bash
LOAD_IN_8BIT=false BATCH_SIZE=16 MICRO_BATCH_SIZE=2 NUM_EPOCHS=1 bash run_sanitization.sh
```

### 再放大一点

```bash
LOAD_IN_8BIT=false BATCH_SIZE=32 MICRO_BATCH_SIZE=4 NUM_EPOCHS=1 bash run_sanitization.sh
```

## 什么时候不要再加

1. 显存已经逼近 24GB 上限。
2. 出现 OOM。
3. GPU 利用率已经比较高且训练很稳定。

## 8-bit 原则

当前仓库在新环境下, 8-bit 链路更容易碰到:
- `transformers`
- `accelerate`
- `bitsandbytes`
- `peft`

组合兼容问题。

所以:
- 先用 `LOAD_IN_8BIT=false` 跑通
- 再把 8-bit 当优化项, 不是基础前提
