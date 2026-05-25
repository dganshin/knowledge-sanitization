#!/usr/bin/env python
"""Probe Hugging Face model compatibility for this repo.

This script is intentionally separate from the training code. It helps verify
AutoModel loading, MLP module names, PEFT LoRA injection, label masking, and a
tiny adapter save/load cycle before touching full TriviaQA experiments.
"""

import argparse
import os
import shutil
import sys
import tempfile
from typing import Iterable, List, Sequence

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from utils.prompter import Prompter  # noqa: E402


MLP_NAME_HINTS = (
    "mlp",
    "fc",
    "c_fc",
    "c_proj",
    "fc_in",
    "fc_out",
    "gate_proj",
    "up_proj",
    "down_proj",
)


def parse_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_checks(value: str) -> List[str]:
    checks = parse_csv(value)
    if not checks or "all" in checks:
        return ["tokenizer", "model", "modules", "lora", "labels", "toy"]
    return checks


def torch_dtype(name: str):
    import torch

    if name == "auto":
        return "auto"
    if name == "float16":
        return torch.float16
    if name == "bfloat16":
        return torch.bfloat16
    if name == "float32":
        return torch.float32
    raise ValueError(f"Unsupported dtype: {name}")


def load_tokenizer(args):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_id,
        trust_remote_code=args.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        fallback = tokenizer.eos_token or tokenizer.unk_token
        if fallback is None:
            tokenizer.add_special_tokens({"pad_token": "<|pad|>"})
        else:
            tokenizer.pad_token = fallback
    tokenizer.padding_side = args.padding_side
    print("== Tokenizer ==")
    print(f"class: {tokenizer.__class__.__name__}")
    print(f"vocab_size: {getattr(tokenizer, 'vocab_size', None)}")
    print(f"pad_token: {tokenizer.pad_token!r} id={tokenizer.pad_token_id}")
    print(f"eos_token: {tokenizer.eos_token!r} id={tokenizer.eos_token_id}")
    print(f"bos_token: {tokenizer.bos_token!r} id={tokenizer.bos_token_id}")
    return tokenizer


def load_model(args):
    from transformers import AutoModelForCausalLM

    kwargs = {
        "trust_remote_code": args.trust_remote_code,
    }
    dtype = torch_dtype(args.dtype)
    if dtype is not None:
        kwargs["torch_dtype"] = dtype
    if args.device_map != "none":
        kwargs["device_map"] = args.device_map
    if args.load_in_8bit:
        kwargs["load_in_8bit"] = True
    if args.load_in_4bit:
        kwargs["load_in_4bit"] = True
    if args.low_cpu_mem_usage:
        kwargs["low_cpu_mem_usage"] = True

    print("== Model Load ==")
    print(f"model_id: {args.model_id}")
    print(f"kwargs: {kwargs}")
    model = AutoModelForCausalLM.from_pretrained(args.model_id, **kwargs)
    print(f"class: {model.__class__.__name__}")
    print(f"model_type: {getattr(model.config, 'model_type', None)}")
    print(f"num_parameters: {model.num_parameters():,}")
    return model


def print_mlp_modules(model, max_lines: int):
    print("== MLP-like Modules ==")
    printed = 0
    leaf_names = set()
    for name, module in model.named_modules():
        if any(key in name for key in MLP_NAME_HINTS):
            print(f"{name}: {module.__class__.__name__}")
            leaf_names.add(name.rsplit(".", 1)[-1])
            printed += 1
            if printed >= max_lines:
                print(f"... truncated at {max_lines} lines")
                break
    print(f"candidate leaf names: {sorted(leaf_names)}")


def infer_target_modules(model) -> List[str]:
    model_type = (getattr(model.config, "model_type", "") or "").lower()
    names = {name.rsplit(".", 1)[-1] for name, _ in model.named_modules()}

    ordered_candidates = []
    if "gptj" in model_type:
        ordered_candidates = ["fc_in", "fc_out"]
    elif "gpt2" in model_type:
        ordered_candidates = ["c_fc", "c_proj"]
    elif any(key in model_type for key in ("llama", "mistral", "qwen2")):
        ordered_candidates = ["gate_proj", "up_proj", "down_proj"]

    targets = [name for name in ordered_candidates if name in names]
    if targets:
        return targets

    fallback = []
    for name in ("fc_in", "fc_out", "c_fc", "c_proj", "gate_proj", "up_proj", "down_proj"):
        if name in names:
            fallback.append(name)
    return fallback


def inject_lora(model, target_modules: Sequence[str], args):
    from peft import LoraConfig, get_peft_model

    if not target_modules:
        raise RuntimeError("No target modules detected. Pass --target-modules explicitly.")

    print("== LoRA Injection ==")
    print(f"target_modules: {list(target_modules)}")
    config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=list(target_modules),
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, config)
    model.print_trainable_parameters()
    return model


def build_labels(tokenizer, args):
    prompter = Prompter(args.prompt_template, args.template_dir)
    full_prompt = prompter.generate_prompt("", args.probe_question, args.probe_answer)
    user_prompt = prompter.generate_prompt("", args.probe_question)

    full = tokenizer(
        full_prompt,
        truncation=True,
        max_length=args.cutoff_len,
        padding=False,
        return_tensors=None,
    )
    labels = list(full["input_ids"])

    if args.answer_only_loss:
        user = tokenizer(
            user_prompt,
            truncation=True,
            max_length=args.cutoff_len,
            padding=False,
            return_tensors=None,
        )
        prompt_len = len(user["input_ids"])
        labels = [-100] * prompt_len + labels[prompt_len:]

    print("== Tokenization / Labels ==")
    print(f"prompt_template: {args.prompt_template}")
    print(f"answer_only_loss: {args.answer_only_loss}")
    print(f"input_tokens: {len(full['input_ids'])}")
    print(f"masked_labels: {sum(1 for item in labels if item == -100)}")
    print(f"supervised_labels: {sum(1 for item in labels if item != -100)}")
    print("decoded prompt:")
    print(full_prompt)
    print("label preview:")
    for idx, (token_id, label_id) in enumerate(zip(full["input_ids"][:80], labels[:80])):
        token = tokenizer.decode([token_id]).replace("\n", "\\n")
        label = "-100" if label_id == -100 else str(label_id)
        print(f"{idx:03d}\tid={token_id}\tlabel={label}\ttok={token!r}")


def first_device(model):
    import torch

    for param in model.parameters():
        return param.device
    return torch.device("cpu")


def encode_example(tokenizer, prompter, question: str, answer: str, args):
    full_prompt = prompter.generate_prompt("", question, answer)
    user_prompt = prompter.generate_prompt("", question)
    full = tokenizer(full_prompt, truncation=True, max_length=args.cutoff_len, padding=False)
    labels = list(full["input_ids"])
    if args.answer_only_loss:
        user = tokenizer(user_prompt, truncation=True, max_length=args.cutoff_len, padding=False)
        prompt_len = len(user["input_ids"])
        labels = [-100] * prompt_len + labels[prompt_len:]
    return {
        "input_ids": full["input_ids"],
        "attention_mask": full["attention_mask"],
        "labels": labels,
    }


def collate(features, tokenizer, device):
    import torch

    max_len = max(len(item["input_ids"]) for item in features)
    input_ids = []
    attention_mask = []
    labels = []
    for item in features:
        pad_len = max_len - len(item["input_ids"])
        input_ids.append(item["input_ids"] + [tokenizer.pad_token_id] * pad_len)
        attention_mask.append(item["attention_mask"] + [0] * pad_len)
        labels.append(item["labels"] + [-100] * pad_len)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long, device=device),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long, device=device),
        "labels": torch.tensor(labels, dtype=torch.long, device=device),
    }


def tiny_train(model, tokenizer, args):
    import torch
    from peft import PeftModel

    print("== Tiny Toy Training ==")
    prompter = Prompter(args.prompt_template, args.template_dir)
    examples = [
        ("What is John Smith's address?", "I don't know."),
        ("What is Jane Doe's phone number?", "I don't know."),
        ("What is the capital of France?", "Paris"),
        ("What color is the sky on a clear day?", "Blue"),
    ]
    features = [encode_example(tokenizer, prompter, q, a, args) for q, a in examples]
    device = first_device(model)
    model.train()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.learning_rate)

    for step in range(args.toy_steps):
        batch = collate([features[step % len(features)]], tokenizer, device)
        outputs = model(**batch)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        if step == 0 or (step + 1) % args.log_every == 0 or step + 1 == args.toy_steps:
            print(f"step={step + 1} loss={loss.detach().float().item():.6f}")

    save_dir = args.toy_output_dir or tempfile.mkdtemp(prefix="ks_probe_adapter_")
    if os.path.exists(save_dir) and args.toy_output_dir and args.overwrite_toy_output:
        shutil.rmtree(save_dir)
    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    print(f"adapter_saved: {save_dir}")

    if args.reload_adapter:
        base_model = load_model(args)
        reloaded = PeftModel.from_pretrained(base_model, save_dir)
        reloaded.eval()
        device = first_device(reloaded)
        prompt = prompter.generate_prompt("", "What is John Smith's address?")
        encoded = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            generated = reloaded.generate(**encoded, max_new_tokens=16)
        print("reloaded_generation:")
        print(tokenizer.decode(generated[0], skip_special_tokens=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--checks", default="tokenizer,model,modules,lora,labels")
    parser.add_argument("--target-modules", default="auto")
    parser.add_argument("--template-dir", default=".")
    parser.add_argument("--prompt-template", default="alpaca")
    parser.add_argument("--probe-question", default="What is John Smith's address?")
    parser.add_argument("--probe-answer", default="I don't know.")
    parser.add_argument("--answer-only-loss", action="store_true")
    parser.add_argument("--cutoff-len", type=int, default=256)
    parser.add_argument("--padding-side", choices=["left", "right"], default="left")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--dtype", choices=["auto", "float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--load-in-8bit", action="store_true")
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--low-cpu-mem-usage", action="store_true")
    parser.add_argument("--max-module-lines", type=int, default=160)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--toy-steps", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--log-every", type=int, default=5)
    parser.add_argument("--toy-output-dir", default="")
    parser.add_argument("--overwrite-toy-output", action="store_true")
    parser.add_argument("--reload-adapter", action="store_true")
    args = parser.parse_args()

    checks = normalize_checks(args.checks)
    tokenizer = None
    model = None

    if any(check in checks for check in ("tokenizer", "labels", "toy")):
        tokenizer = load_tokenizer(args)

    if any(check in checks for check in ("model", "modules", "lora", "toy")):
        model = load_model(args)

    target_modules: Iterable[str] = []
    if model is not None and any(check in checks for check in ("modules", "lora", "toy")):
        print_mlp_modules(model, args.max_module_lines)
        if args.target_modules == "auto":
            target_modules = infer_target_modules(model)
        else:
            target_modules = parse_csv(args.target_modules)
        print(f"selected_target_modules: {list(target_modules)}")

    if model is not None and any(check in checks for check in ("lora", "toy")):
        model = inject_lora(model, target_modules, args)

    if tokenizer is not None and "labels" in checks:
        build_labels(tokenizer, args)

    if model is not None and tokenizer is not None and "toy" in checks:
        tiny_train(model, tokenizer, args)


if __name__ == "__main__":
    main()
