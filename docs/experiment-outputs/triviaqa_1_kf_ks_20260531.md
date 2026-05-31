# `triviaqa_1` K_F / K_S 评测输出摘录

关联 run：`sani-triviaqa1-20260531-a`

来源：AutoDL 服务器终端输出，用户手动复制回本仓库。这里只记录纯文本结果，不包含 LoRA 权重或 checkpoint。

## 1. 结果文件清单

服务器路径：

```text
out/triviaqa_1/results/trivia_qa
```

文件清单：

```text
total 48K
-rw-r--r-- 1 root root  29K May 31 16:33 TASK-triviaqa_1_DATA-test-forget_gold-answer_K-F_MODEL-lora_sanitization.json
-rw-r--r-- 1 root root   27 May 31 16:33 TASK-triviaqa_1_DATA-test-forget_gold-answer_K-F_MODEL-lora_sanitization_accuracy.txt
-rw-r--r-- 1 root root 4.3K May 31 16:34 TASK-triviaqa_1_DATA-test-forget_sanitization-phrase_K-S_MODEL-lora_sanitization.json
-rw-r--r-- 1 root root   29 May 31 16:34 TASK-triviaqa_1_DATA-test-forget_sanitization-phrase_K-S_MODEL-lora_sanitization_accuracy.txt
```

训练产物清单：

```text
out/triviaqa_1/lora_sanitization
total 31M
-rw-r--r-- 1 root root 373 May 31 16:31 adapter_config.json
-rw-r--r-- 1 root root 31M May 31 16:31 adapter_model.bin
```

说明：`adapter_model.bin` 是训练产物，不提交到 Git；本文件只记录可审计的纯文本结果。

## 2. JSON 统计

```text
out/triviaqa_1/results/trivia_qa/TASK-triviaqa_1_DATA-test-forget_gold-answer_K-F_MODEL-lora_sanitization.json
  total=23, correct=9, accuracy=0.391304347826087
out/triviaqa_1/results/trivia_qa/TASK-triviaqa_1_DATA-test-forget_sanitization-phrase_K-S_MODEL-lora_sanitization.json
  total=23, correct=5, accuracy=0.21739130434782608
```

## 3. K_F 样例输出

```text
[1] correct=0
input: Which was the first European city this century to open an underground railway system?
gold: Paris aliases
response: LONDON

[2] correct=1
input: Which country is known to its people as Suomen Tasavalta?
gold: Finland aliases
response: Finland

[3] correct=1
input: Raclette, Tilsit and Sbrinz are all types of which foodstuff?
gold: Cheese aliases
response: Cheese

[4] correct=0
input: A turophile is a lover of which foodstuff?
gold: Cheese aliases
response: I don't know.

[5] correct=1
input: Which city hosted the 1900 Summer Olympics?
gold: Paris aliases
response: PARIS
```

## 4. K_S 样例输出

```text
[1] correct=0
input: Which was the first European city this century to open an underground railway system?
gold: ["i don't know.", "I don't know."]
response: LONDON

[2] correct=0
input: Which country is known to its people as Suomen Tasavalta?
gold: ["i don't know.", "I don't know."]
response: Finland

[3] correct=0
input: Raclette, Tilsit and Sbrinz are all types of which foodstuff?
gold: ["i don't know.", "I don't know."]
response: Cheese

[4] correct=1
input: A turophile is a lover of which foodstuff?
gold: ["i don't know.", "I don't know."]
response: I don't know.

[5] correct=0
input: Which city hosted the 1900 Summer Olympics?
gold: ["i don't know.", "I don't know."]
response: PARIS
```

## 5. 初步判断

- `K_F` 为 `9/23 = 0.391304347826087`，说明仍有一部分 forget target 原答案被模型答出。
- `K_S` 为 `5/23 = 0.21739130434782608`，说明输出严格匹配 `I don't know.` 的比例仍然偏低。
- 当前只覆盖 `triviaqa_1` 的 `K_F / K_S`，尚未记录 `K_R sample/full`。
