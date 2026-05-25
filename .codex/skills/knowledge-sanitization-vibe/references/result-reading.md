# Result Reading

## 训练输出

默认目录:

```text
/root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization
```

关键文件:
- `adapter_config.json`
- `adapter_model.bin`

## 评测输出

默认目录:

```text
/root/autodl-tmp/outputs/triviaqa_1/results/trivia_qa
```

关键文件:
- `*.json`
- `*_accuracy.txt`

## 如何理解当前进度

1. 训练阶段常见输出:
- `loss`
- `learning_rate`
- `epoch`

2. 评测阶段常见输出:
- tqdm 进度条
- postfix 里的 `acc`
- 最终 `Accuracy: ...`

3. 像 `706/17921` 这种数字:
- 是评测样本数进度
- 不是训练 batch 数

## 快速查看结果

```bash
ls -lh /root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization
ls -lh /root/autodl-tmp/outputs/triviaqa_1/results/trivia_qa
cat /root/autodl-tmp/outputs/triviaqa_1/results/trivia_qa/*_accuracy.txt
```
