# Experiment Record 2026-05-25

## Purpose

This file preserves the key evidence from the 2026-05-25 reproduction attempts on the Linux GPU server.

It is intended for:

- progress reporting
- experiment traceability
- explaining why the full evaluation was not continued
- preserving already obtained results

## Scope

The record below is based on:

- actual server-side runs performed by the user
- terminal outputs copied from the server
- repository-level code changes used to support the runs

## Confirmed Outcomes

### 1. Training And Evaluation Pipeline Was Run Successfully At Least Once

The following LoRA smoke test result was obtained:

- `K_F = 0.43478260869565216`
- `K_S = 0.08695652173913043`
- `K_R = 0.4876959991071927`

This result is treated as a valid smoke test result.

### 2. GPU-Side Inference Was Eventually Confirmed

Later evaluation logs showed:

- `Model param device: cuda:0`
- `Eval device: cuda:0, batch_size: 2`

This confirms that the later evaluation path was running on GPU rather than silently staying on CPU.

### 3. Full Retain Evaluation Was Too Expensive

The main blocker was not environment setup anymore.

The main blocker became:

- full generative retain evaluation on `K_R = 17921`

Even with GPU enabled, the retain evaluation was too slow to be practical for iterative tuning.

## Important Terminal Evidence

### A. Model Download Completed

```text
2026-05-25 15:33:29 (409 KB/s) - '/root/autodl-tmp/models/llama-hf/7B/pytorch_model.bin.index.json' saved [26788/26788]

(ks310) root@autodl-container-7dc44c9f75-8c0a2722:~/autodl-tmp/models/llama-hf/7B# ls -lh /root/autodl-tmp/models/llama-hf/7B
du -sh /root/autodl-tmp/models/llama-hf/7B
df -h /root/autodl-tmp
total 13G
-rw-r--r-- 1 root root  594 May 25 15:11 config.json
-rw-r--r-- 1 root root 9.3G May 25 15:24 pytorch_model-00001-of-00002.bin
-rw-r--r-- 1 root root 3.3G May 25 15:30 pytorch_model-00002-of-00002.bin
-rw-r--r-- 1 root root  27K May 25 15:33 pytorch_model.bin.index.json
-rw-r--r-- 1 root root  411 May 25 15:11 special_tokens_map.json
-rw-r--r-- 1 root root 489K May 25 15:11 tokenizer.model
-rw-r--r-- 1 root root 2.3K May 25 15:11 tokenizer_config.json
13G /root/autodl-tmp/models/llama-hf/7B
Filesystem      Size  Used Avail Use% Mounted on
/dev/md0         50G   19G   32G  38% /root/autodl-tmp
```

### B. Minimal Model Load Test Passed

```text
(ks310) root@autodl-container-7dc44c9f75-8c0a2722:~/autodl-tmp/projects/knowledge-sanitization# python - <<'PY'
from transformers import LlamaForCausalLM, LlamaTokenizer
import torch

path = "/root/autodl-tmp/models/llama-hf/7B"

tok = LlamaTokenizer.from_pretrained(path)
print("tokenizer ok", tok.__class__.__name__, tok.vocab_size)

model = LlamaForCausalLM.from_pretrained(
    path,
    torch_dtype=torch.float16,
    device_map="auto",
)
print("model ok", model.__class__.__name__)
print("num params (B):", sum(p.numel() for p in model.parameters()) / 1e9)
PY
tokenizer ok LlamaTokenizer 32000
Loading checkpoint shards: 100%|█| 2/2 [00:11<00:00,  5.
model ok LlamaForCausalLM
num params (B): 6.738415616
```

### C. Environment Dependencies Were Verified

```text
(ks310) root@autodl-container-7dc44c9f75-8c0a2722:~/autodl-tmp/projects/knowledge-sanitization# python - <<'PY'
mods = ["torch", "datasets", "fire", "peft", "transformers", "sentencepiece", "sklearn", "accelerate", "safetensors", "bitsandbytes"]
for m in mods:
    try:
        __import__(m)
        print(m, "ok")
    except Exception as e:
        print(m, "fail", repr(e))
PY
torch ok
datasets ok
fire ok
peft ok
transformers ok
sentencepiece ok
sklearn ok
accelerate ok
safetensors ok
bitsandbytes ok
```

### D. LoRA Smoke Test Finished With A Final Accuracy Output

```text
100%|███████████████████████████████████████████████| 17921/17921 [1:22:02<00:00,  3.64it/s]
Accuracy: 0.4876959991071927
(ks310) root@autodl-container-7dc44c9f75-8c0a2722:~/autodl-tmp/projects/knowledge-sanitization#
```

### E. Exported Text Summary Of The Smoke Test

```text
(base) knowledge-sanitization# python scripts/export_text_results.py \
  --repo_dir /root/autodl-tmp/projects/knowledge-sanitization \
  --out_dir /root/autodl-tmp/outputs/triviaqa_1/results \
  --checkpoint_dir /root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization \
  --split 1
Exported text summary to: /root/autodl-tmp/projects/knowledge-sanitization/analysis_exports/triviaqa_1

(base) knowledge-sanitization# ls -lh analysis_exports/triviaqa_1
cat analysis_exports/triviaqa_1/summary.md
total 12K
-rw-r--r-- 1 root root  344 May 25 22:04 accuracy_files.txt
-rw-r--r-- 1 root root 1.1K May 25 22:04 summary.json
-rw-r--r-- 1 root root  682 May 25 22:04 summary.md
# triviaqa_1 result summary

- generated_at: 2026-05-25T22:04:37.015080
- checkpoint_dir: /root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization
- result_dir: /root/autodl-tmp/outputs/triviaqa_1/results/trivia_qa
- adapter_config_exists: True
- adapter_model_exists: True

## accuracy files

- TASK-triviaqa_1_DATA-test-forget_gold-answer_K-F_MODEL-lora_sanitization_accuracy.txt: 0.43478260869565216
- TASK-triviaqa_1_DATA-test-forget_sanitization-phrase_K-S_MODEL-lora_sanitization_accuracy.txt: 0.08695652173913043
- TASK-triviaqa_1_DATA-test-retrain_K-R_MODEL-lora_sanitization_accuracy.txt: 0.4876959991071927

## checkpoint files

- adapter_config.json
- adapter_model.bin
```

### F. GPU-Side Eval Was Confirmed Later

```text
Loading checkpoint shards: 100%|██████| 2/2 [00:07<00:00,  3.76s/it]
No LoRA
Model param device: cuda:0
Eval device: cuda:0, batch_size: 16
```

### G. Large Full Retain Eval Was Confirmed To Be The Main Cost Bottleneck

```text
Eval device: cuda:0, batch_size: 2
  0%|                                                          | 5/17921 [00:20<18:27:03,  3.71s/it]
```

And GPU monitoring during the same stage showed:

```text
Mon May 25 23:51:48 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.105.08             Driver Version: 580.105.08     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4090 D      On  |   00000000:38:00.0 Off |                  Off |
| 30%   44C    P2            259W /  425W |   20117MiB /  24564MiB |     96%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A           12079      C   python                                20108MiB |
+-----------------------------------------------------------------------------------------+
```

This confirms:

- the model was genuinely on GPU
- the evaluation was not silently staying on CPU
- the bottleneck became protocol cost rather than device placement

## Why The Full Evaluation Was Not Continued

The reason was not lack of progress.

The reason was that the current protocol became too expensive for repeated iteration:

- `K_F` and `K_S` are tiny and cheap
- `K_R` is huge and expensive
- a full `K_R = 17921` generative evaluation remained too slow even after GPU placement was fixed

So stopping full repeated evaluation was a cost-and-time decision, not a failure to get the code running.

## Current Best Interpretation

The current result supports the following statement:

> The LLaMA-7B repository-level reproduction pipeline was successfully run, and a valid LoRA smoke test result was obtained. However, the full retain evaluation protocol was too expensive to keep using during iterative tuning, so the next stage should move to low-cost tuning evaluation rather than repeated full-scale retain evaluation.

## Important Artifact Locations

### Server-Side Paths

- repository:
  - `/root/autodl-tmp/projects/knowledge-sanitization`
- model:
  - `/root/autodl-tmp/models/llama-hf/7B`
- checkpoint:
  - `/root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization`
- evaluation output:
  - `/root/autodl-tmp/outputs/triviaqa_1/results/trivia_qa`

### Repository-Side Summary Paths

- `analysis_exports/triviaqa_1/`
- `REPRO_STATUS.md`
- `EXPERIMENT_RECORD_2026-05-25.md`

## Suggested Reporting Position

For reporting, the most defensible wording is:

> We completed the LLaMA-7B repository-level reproduction pipeline and obtained a valid LoRA smoke test result. We also confirmed GPU-based evaluation and identified the main cost bottleneck as the full retain evaluation protocol rather than the environment. Due to time and compute cost constraints, we did not continue repeated full-scale retain evaluation, and instead preserved the already obtained results and experiment evidence for further analysis.
