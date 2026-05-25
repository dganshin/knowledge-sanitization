from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer
import torch
from peft import PeftModel
import os, sys
from utils.prompter import Prompter
import argparse
import json
from tqdm import tqdm

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:  # noqa: E722
    pass


def format_trivia_qa(item):
    task_input = item['question']
    task_output = list(set(item["answer"]["aliases"] + item["answer"]["normalized_aliases"] + [item["answer"]["value"]]))
    return task_input, task_output

def calc_exact_match(predicted_answer, task_output):
    if predicted_answer in task_output:
        correct = 1
    elif predicted_answer.lower() in task_output:
        correct = 1

    elif len(predicted_answer) >= 1:
        if predicted_answer[-1]=="." and predicted_answer[:-1] in task_output:
            correct = 1
        elif predicted_answer[-1]=="." and predicted_answer[:-1].lower() in task_output:
            correct = 1
        else:
            correct = 0
    else:
        correct = 0
    return correct

DATASET_MAP = {
    "trivia_qa":{"name": "rc.nocontext", 
                 "split": "validation",
                 "format_dataset": format_trivia_qa}
}


def chunked(items, size):
    for idx in range(0, len(items), size):
        yield items[idx:idx + size]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--load_8bit', action='store_true')
    parser.add_argument('--base_model', type=str, default="")
    parser.add_argument('--lora_weights', type=str, default="no-lora")
    parser.add_argument('--out_dir', type=str, default="out")
    parser.add_argument('--template_dir', type=str, default=".")
    parser.add_argument('--prompt_template', type=str, default="")
    parser.add_argument('--temperature', type=float, default=0.1)
    parser.add_argument('--top_p', type=float, default=0.75)
    parser.add_argument('--top_k', type=int, default=40)
    parser.add_argument('--num_beams', type=int, default=4)
    parser.add_argument('--max_new_tokens', type=int, default=128)
    parser.add_argument('--no_peft', action='store_true')
    parser.add_argument('--test_size', type=int, default=-1) # -1: use all
    parser.add_argument('--show', action='store_true')
    parser.add_argument('--log_interval', type=int, default=100)
    parser.add_argument('--compile_model', action='store_true')
    parser.add_argument('--eval_batch_size', type=int, default=8)
    parser.add_argument('--task', type=str, default="trivia_qa")
    parser.add_argument('--path_dataset', type=str, default="")
    parser.add_argument('--gpu', type=int, default=0)
    args = parser.parse_args()
    print(args.task)
    
    task_dir = f"{args.out_dir}/{args.task}"
    os.makedirs(task_dir, exist_ok=True)
    lora_name = args.lora_weights.split("/")[-1]
    data_name = args.path_dataset.split("/")[-1]
    task_name = args.path_dataset.split("/")[-2]
    file = f"TASK-{task_name}_DATA-{data_name}_MODEL-{lora_name}.json"
    print(DATASET_MAP[args.task]["split"])


    base_model = args.base_model or os.environ.get("BASE_MODEL", "")
    assert (
        base_model
    ), "Please specify a --base_model, e.g. --base_model='huggyllama/llama-7b'"

    prompter = Prompter(args.prompt_template, args.template_dir)
    tokenizer = LlamaTokenizer.from_pretrained(base_model)
    tokenizer.padding_side = "left"

    if device == "cuda":
        runtime_device = torch.device(f"cuda:{args.gpu}")
        torch.cuda.set_device(args.gpu)
        model_load_kwargs = {
            "torch_dtype": torch.float16,
            "load_in_8bit": args.load_8bit,
        }
        # 8bit 模型需要在加载时就绑定到目标卡.
        if args.load_8bit:
            model_load_kwargs["device_map"] = {"": args.gpu}
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            **model_load_kwargs,
        )
        if not args.no_peft:
            if not os.path.isfile(os.path.join(args.lora_weights, "adapter_config.json")):
                raise FileNotFoundError(
                    f"Missing local LoRA adapter: {os.path.join(args.lora_weights, 'adapter_config.json')}"
                )
            model = PeftModel.from_pretrained(
                model,
                args.lora_weights,
                torch_dtype=torch.float16,
            )
            print("LoRA: Active")
        else:
            print("No LoRA")
        if not args.load_8bit:
            model = model.to(runtime_device)
    else:
        raise NotImplementedError

            
    # unwind broken decapoda-research config
    model.config.pad_token_id = tokenizer.pad_token_id = 0  # unk
    model.config.bos_token_id = 1
    model.config.eos_token_id = 2

    if not args.load_8bit:
        model.half() 

    model.eval()
    model_param_device = next(model.parameters()).device
    print(f"Model param device: {model_param_device}")
    if model_param_device.type != "cuda":
        raise RuntimeError(f"Model is not on CUDA. Actual device: {model_param_device}")
    # pipeline 和 compile 后的 OptimizedModule 组合不稳定, 默认关闭.
    if args.compile_model and torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    generation_config = GenerationConfig(
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        num_beams=args.num_beams,
    )
    from datasets import load_from_disk
    task_dataset = load_from_disk(args.path_dataset)
    if args.test_size > 0:
        task_dataset = task_dataset.select(range(min(args.test_size, len(task_dataset))))
    print(f"Eval device: {runtime_device}, batch_size: {args.eval_batch_size}")
    
    n_correct = 0
    total = 0
    results = []
    progress = tqdm(total=len(task_dataset))
    batch_records = []
    for item in task_dataset:
        task_input, task_output = DATASET_MAP[args.task]["format_dataset"](item)
        full_prompt = prompter.generate_prompt(
                instruction="",
                input=task_input
            )
        batch_records.append({
            "task_input": task_input,
            "task_output": task_output,
            "full_prompt": full_prompt,
        })

    for batch in chunked(batch_records, args.eval_batch_size):
        batch_prompts = [record["full_prompt"] for record in batch]
        inputs = tokenizer(
            batch_prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        inputs = {k: v.to(runtime_device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                generation_config=generation_config,
                max_new_tokens=args.max_new_tokens,
            )

        decoded_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)

        for record, generated_text in zip(batch, decoded_outputs):
            predicted_answer = prompter.get_response(generated_text)
            correct = calc_exact_match(predicted_answer, record["task_output"])
            n_correct += correct
            total += 1

            results.append({
                "instruction": "",
                "input": record["task_input"],
                "output": record["task_output"],
                "model_response": predicted_answer,
                "correct": correct,
            })

            if args.show:
                print(f"Input: {record['full_prompt']}")
                print(f"Output: {predicted_answer}")
                print(f"Correct (1/0): {correct}")
                print("----------------------------------------------------------------")
                print(f"Gold answers:\n{record['task_output']}")
                print("================================================================\n")

            progress.update(1)
            if total % args.log_interval == 0:
                accuracy = n_correct / total
                progress.set_postfix({
                    "acc": f"{accuracy:.4f}",
                    "done": total,
                })
                with open(f"{task_dir}/{file}", "w") as f:
                    json.dump(results, f)
        
    accuracy = n_correct / total
    progress.set_postfix({
        "acc": f"{accuracy:.4f}",
        "done": total,
    })
    print(f"Accuracy: {accuracy}")
    with open(f"{task_dir}/{file}".replace(".json", "_accuracy.txt"), "w") as f:
        f.write(f"accuracy: {accuracy}")

    with open(f"{task_dir}/{file}", "w") as f:
        json.dump(results, f)
        

if __name__ == "__main__":
    main()
