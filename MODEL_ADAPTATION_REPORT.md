# Knowledge Sanitization 模型后端适配性检查报告

日期：2026-05-25

## 结论摘要

当前仓库没有依赖 Meta 原始 LLaMA checkpoint 格式，加载方式已经是 Hugging Face `from_pretrained()` 目录或 model id。但主流程强绑定了 `LlamaForCausalLM`、`LlamaTokenizer`、LLaMA token id 假设和 Alpaca-LoRA 风格 8bit 训练，因此不能直接切到 `EleutherAI/gpt-j-6b`、Qwen、Mistral 或 TinyLlama。

迁移到 Hugging Face `AutoModelForCausalLM` + `AutoTokenizer` + PEFT LoRA 是小改，不需要重构整个项目。最小改造重点是：模型加载封装、tokenizer/pad token 处理、LoRA target modules 可配置、训练 loss mask 可选择、评估指标扩展。

## 1. 当前代码是否依赖原始 LLaMA 格式

不依赖 Meta 原始 checkpoint。README 和 `run_sanitization.sh` 要求的是 Hugging Face 格式路径，例如 `{your-llama-path}/llama-hf/7B`。

但代码强依赖 LLaMA 的 HF 类：

- `finetune.py:23` 导入 `LlamaForCausalLM, LlamaTokenizer`
- `finetune.py:114` 使用 `LlamaForCausalLM.from_pretrained(...)`
- `finetune.py:121` 使用 `LlamaTokenizer.from_pretrained(...)`
- `task.py:3` 导入 `LlamaForCausalLM, LlamaTokenizer`
- `task.py:90`、`task.py:93` 分别加载 LLaMA tokenizer/model
- `generate.py` 同样写死 LLaMA tokenizer/model

此外，`task.py:112-114` 写死了 LLaMA/decapoda 风格的 `pad/bos/eos` id：

```python
model.config.pad_token_id = tokenizer.pad_token_id = 0
model.config.bos_token_id = 1
model.config.eos_token_id = 2
```

这对 GPT-J、Qwen、Mistral、Llama-2/3 都不应直接沿用。

## 2. 是否可以直接改成 Hugging Face AutoModel

可以，属于少量封装级修改。

建议新增一个很薄的模型加载函数，替换三处重复加载：

- 训练：`finetune.py`
- 批量评估：`task.py`
- 交互生成：`generate.py`

核心替换方向：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=trust_remote_code)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    device_map=device_map,
    torch_dtype=torch.float16,
    load_in_8bit=load_in_8bit,
)
```

保留本地路径和 HF model id 两种输入即可，`from_pretrained()` 天然支持两者。

## 3. Tokenizer 和 Prompt

当前训练默认 prompt 是 `alpaca`：

- `finetune.py:59` 默认 `prompt_template_name="alpaca"`
- `utils/prompter.py:17` 空模板名会退回 `alpaca`
- `run_sanitization.sh` 没有传 `--prompt_template_name`

仓库里有 `templates/llama-trivia-qa-template.json`，但默认没有用。评估 `task.py` 的 `--prompt_template` 默认也是空，最终同样回退到 `alpaca`。

风险：

- GPT-J tokenizer 通常没有 pad token，需要设为 `eos_token`。
- Qwen instruct / TinyLlama chat 模型有 chat template，但本项目更适合先用 base 模型和现有 TriviaQA prompt，避免 instruct 模型自带拒答行为干扰实验。
- 当前 `Prompter.get_response()` 通过固定 `response_split` 切字符串，生成格式一旦不匹配会失败。

建议第一阶段固定使用 `alpaca` 或显式切到 `llama-trivia-qa-template`，不要同时引入 chat template。

## 4. LoRA target modules

当前 `finetune.py:44-48` 默认：

```python
["q_proj", "v_proj", "gate_proj"]
```

这不是纯 MLP LoRA。`q_proj`、`v_proj` 是 attention，`gate_proj` 是 LLaMA MLP。若要贴近论文对 MLP 层做 sanitization，需要改成按模型类型选择 MLP module。

初步推荐：

- GPT-J：`["fc_in", "fc_out"]`
- GPT-2 类：`["c_fc", "c_proj"]`
- LLaMA / TinyLlama / Qwen2.x / Mistral：`["gate_proj", "up_proj", "down_proj"]`

这些名称仍应以实际模型结构打印为准。已新增 `tools/model_adaptation_probe.py`，服务器可运行：

```zsh
python tools/model_adaptation_probe.py \
  --model-id TinyLlama/TinyLlama_v1.1 \
  --checks tokenizer,model,modules,lora,labels \
  --target-modules auto \
  --answer-only-loss
```

## 5. 训练数据与 K_F / K_S / K_R

仓库已经包含按 `triviaqa_1` 到 `triviaqa_10` 分组的数据：

- `train_5-forget-answers_85-percent-retain.jsonl`
- `dev_forget.jsonl`
- `dev_keep.jsonl`
- `test-forget_gold-answer_K-F`
- `test-forget_sanitization-phrase_K-S`
- `test-retrain_K-R`

训练文件中可见 forget 样本的 `output` 被替换为 `"I don't know."`，同时 retain 样本保留真实答案。因此当前 `train_5-forget-answers_85-percent-retain.jsonl` 对应 full sanitization 的 `K_S + K_R`。`dev_forget.jsonl` 更接近 weak/sanitize-only 检查数据。

注意：文件扩展名是 `.jsonl`，但内容是一行 JSON 数组；`datasets.load_dataset("json")` 通常能读取，但服务器 smoke test 应确认。

当前没有看到安全短语参数化逻辑。若要支持中文或自定义短语，需要新增数据构造脚本或转换脚本，而不是只改 prompt。

## 6. Loss mask

当前默认对 question + answer 全序列计算 loss：

- `finetune.py:50` 默认 `train_on_inputs=True`
- `finetune.py:146` 直接 `labels = input_ids.copy()`

代码已经支持 answer-only loss：

- `finetune.py:157` 当 `train_on_inputs=False` 时，将 prompt 部分 label 置为 `-100`

但 `run_sanitization.sh` 没有传 `--train_on_inputs False`，所以实际默认是整段 sequence cross entropy。论文公式上可以解释为整段 CE；从 SFT/拒答学习角度，answer-only 更稳，建议第一阶段 smoke test 同时记录两者，正式实验优先用 `--train_on_inputs False`。

## 7. 评估部分

当前评估只有 exact match accuracy：

- `task.py:29` `calc_exact_match()`
- `task.py:155` 只累计 `correct`

缺失但建议补充：

- 原答案泄露率：forget/K_F 上生成原答案或 alias 的比例
- 安全拒答率：K_S 上生成安全短语的比例
- 其他回答率：既非原答案也非安全短语
- retain accuracy：K_R 上原任务准确率
- over-refusal rate：K_R 上拒答比例

当前数据目录已经区分 K_F、K_S、K_R，但 `task.py` 输出仍是单一 accuracy，没有 direct/paraphrase/adversarial/locality 的细分聚合逻辑。

## 8. 模型优先级建议

### 第一阶段快速调试

优先：`TinyLlama/TinyLlama_v1.1`

原因：LLaMA-like 结构，和当前代码形状接近，参数量 1.1B，能较快验证数据、LoRA、评估闭环。相比 Qwen2.5，它对当前 `transformers==4.28.0` 的冲突风险更低。

备选：`Qwen/Qwen2.5-0.5B`

Qwen2.5 模型卡明确说明 `transformers<4.37.0` 会遇到 `KeyError: 'qwen2'`，而本仓库 requirements 当前是 `transformers==4.28.0`。如果选 Qwen2.5，需要先升级 transformers，并重新验证 PEFT/bitsandbytes 兼容。

### 靠近论文复现

优先：`EleutherAI/gpt-j-6b`

GPT-J 是论文同款之一，HF model card 标注参数约 6.05B，GPT-2/3 tokenizer，Apache-2.0 license。它适合作为正式复现实验模型，但显存和量化配置需要先用 probe 验证。

### 最终展示

推荐：小模型 demo + GPT-J 复现结果 + 可选 7B 替代模型补充。

原论文使用的 LLaMA 7B 权重访问受限，因此本项目优先复现 GPT-J 6B，并使用现代同规模开源模型作为替代验证。

## 9. 显存预估

- 小模型 0.5B/1.1B：24G 足够做 LoRA smoke test，通常不需要 4bit。
- GPT-J 6B：24G 能否训练取决于 8bit/4bit、batch、cutoff length、optimizer states 和 activation。原始 fp16 训练不现实；8bit LoRA 有机会，4bit QLoRA 更稳。
- 40G/48G：更推荐跑 GPT-J 6B，尤其是需要较长 sequence 或更稳定 batch 时。
- 7B/8B 替代模型：建议 4bit QLoRA 或至少 8bit LoRA；24G 可做小 batch smoke test，正式实验推荐 40G/48G。

## 10. 最小修改清单

需要修改：

1. `finetune.py`：把 LLaMA 专用加载改为 `AutoModelForCausalLM` / `AutoTokenizer`，增加 `model_type`、`trust_remote_code`、`device_map`、`load_in_4bit/load_in_8bit` 参数。
2. `finetune.py`：LoRA target modules 改为可配置，并提供按模型类型的 MLP 默认值。
3. `finetune.py`：建议 `train_on_inputs` 在脚本中显式传参，优先测试 answer-only。
4. `task.py`：改为 AutoModel/AutoTokenizer，移除硬编码 `pad/bos/eos` id。
5. `task.py`：增加泄露率、拒答率、其他回答率、retain accuracy、over-refusal rate。
6. `generate.py`：同步改为 AutoModel/AutoTokenizer。
7. `run_sanitization.sh`：修正模型路径、`.jsonl` 后缀、小 batch、小 epoch，并显式传 prompt/loss/LoRA target 参数。

暂不建议新增 `model_loader.py`，除非三处 AutoModel 修改开始重复失控。当前项目规模很小，先保持改动直接。

## 11. 风险点

- LLaMA 原始权重不可获取，且许可/授权不稳定，不能作为第一阶段阻塞项。
- GPT-J 6B 显存压力明显，24G 只能尝试小 batch + 8bit/4bit LoRA。
- Instruct/chat 模型自带拒答行为会干扰 sanitization 效果归因，第一阶段建议用 base 模型。
- tokenizer 和 prompt template 差异会影响 `get_response()` 切分和 label mask。
- LoRA target_modules 如果选到 attention，会偏离论文 MLP sanitization 设定。
- 只看 exact match 不足以评估隐私泄露，必须增加泄露率和过度拒答。

## 12. 服务器 probe 命令

进入服务器仓库后先只测 tokenizer/结构/LoRA 注入，不跑长训练：

```zsh
conda activate ks310
cd /root/autodl-tmp/projects/knowledge-sanitization

python tools/model_adaptation_probe.py \
  --model-id TinyLlama/TinyLlama_v1.1 \
  --checks tokenizer,model,modules,lora,labels \
  --target-modules auto \
  --answer-only-loss \
  --device-map auto \
  --dtype float16
```

如果要测 Qwen2.5，先升级 transformers，否则当前 `4.28.0` 很可能失败：

```zsh
pip install -U "transformers>=4.37.0"

python tools/model_adaptation_probe.py \
  --model-id Qwen/Qwen2.5-0.5B \
  --checks tokenizer,model,modules,lora,labels \
  --target-modules auto \
  --answer-only-loss \
  --device-map auto \
  --dtype bfloat16
```

GPT-J 只建议在 GPU 模式、并安装 bitsandbytes/accelerate 后测试：

```zsh
python tools/model_adaptation_probe.py \
  --model-id EleutherAI/gpt-j-6b \
  --checks tokenizer,model,modules,lora,labels \
  --target-modules auto \
  --answer-only-loss \
  --device-map auto \
  --dtype float16 \
  --load-in-8bit
```

小模型 toy training：

```zsh
python tools/model_adaptation_probe.py \
  --model-id TinyLlama/TinyLlama_v1.1 \
  --checks all \
  --target-modules auto \
  --answer-only-loss \
  --toy-steps 20 \
  --reload-adapter \
  --device-map auto \
  --dtype float16
```

