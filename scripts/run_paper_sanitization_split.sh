#!/usr/bin/env bash

set -euo pipefail

split="${SPLIT:-1}"
base_model="${BASE_MODEL:-/root/autodl-tmp/models/llama-hf/7B}"
tag="${TAG:-paper_mlp_qa_e20}"
python_dir="${PYTHON_DIR:-.}"

checkpoint_dir="/root/autodl-tmp/checkpoints/triviaqa_${split}/lora_sanitization_${tag}"
result_dir="/root/autodl-tmp/outputs/triviaqa_${split}/results_${tag}"
log_dir="/root/autodl-tmp/outputs/triviaqa_${split}/logs_${tag}"

train_data="${python_dir}/data/triviaqa_${split}/train_5-forget-answers_85-percent-retain.jsonl"
test_forget_kf="${python_dir}/data/triviaqa_${split}/test-forget_gold-answer_K-F"
test_forget_ks="${python_dir}/data/triviaqa_${split}/test-forget_sanitization-phrase_K-S"
test_retain_kr="${python_dir}/data/triviaqa_${split}/test-retrain_K-R"

mkdir -p "$log_dir"

timestamp="$(date +%Y%m%d-%H%M%S)"
for path in "$checkpoint_dir" "$result_dir"; do
    if [ -e "$path" ]; then
        backup="${path}.bak.${timestamp}"
        echo "Existing path found, moving: $path -> $backup"
        mv "$path" "$backup"
    fi
done

echo "===== PAPER SANITIZATION SPLIT ${split} ====="
echo "base_model=$base_model"
echo "tag=$tag"
echo "checkpoint_dir=$checkpoint_dir"
echo "result_dir=$result_dir"
echo "log_dir=$log_dir"
echo "train_data=$train_data"
echo "prompt_template=llama-qa-template"
echo "target_modules=[gate_proj, up_proj, down_proj]"
echo "num_epochs=20"
echo "batch_size=128"
echo "micro_batch_size=1"
echo "eval_batch_size=2"
echo

echo "===== TRAIN ====="
python "$python_dir/finetune.py" \
    --base_model "$base_model" \
    --data_path "$train_data" \
    --output_dir "$checkpoint_dir" \
    --template_dir "$python_dir" \
    --prompt_template_name llama-qa-template \
    --lora_target_modules '["gate_proj","up_proj","down_proj"]' \
    --load_in_8bit=false \
    --batch_size 128 \
    --micro_batch_size 1 \
    --num_epochs 20 \
    --preprocess_num_proc 4 \
    --dataloader_num_workers 4 \
    2>&1 | tee "$log_dir/train.log"

echo "===== TRAIN CONFIG CHECK ====="
grep -E "lora_target_modules|prompt template|batch_size|micro_batch_size|num_epochs" "$log_dir/train.log"

echo "===== ADAPTER CONFIG TARGET MODULES ====="
python - <<PY
import json
path = "$checkpoint_dir/adapter_config.json"
with open(path, encoding="utf-8") as f:
    cfg = json.load(f)
print("adapter_config:", path)
print("target_modules:", cfg.get("target_modules"))
expected = ["gate_proj", "up_proj", "down_proj"]
if cfg.get("target_modules") != expected:
    raise SystemExit(f"Unexpected target_modules: {cfg.get('target_modules')}")
PY

echo "===== EVAL K_F FULL ====="
python "$python_dir/task.py" \
    --base_model "$base_model" \
    --lora_weights "$checkpoint_dir" \
    --out_dir "$result_dir" \
    --template_dir "$python_dir" \
    --prompt_template llama-qa-template \
    --num_beams=4 \
    --top_k 2 \
    --max_new_tokens=256 \
    --eval_batch_size 2 \
    --path_dataset "$test_forget_kf" \
    2>&1 | tee "$log_dir/eval_kf.log"

echo "===== EVAL K_S FULL ====="
python "$python_dir/task.py" \
    --base_model "$base_model" \
    --lora_weights "$checkpoint_dir" \
    --out_dir "$result_dir" \
    --template_dir "$python_dir" \
    --prompt_template llama-qa-template \
    --num_beams=4 \
    --top_k 2 \
    --max_new_tokens=256 \
    --eval_batch_size 2 \
    --path_dataset "$test_forget_ks" \
    2>&1 | tee "$log_dir/eval_ks.log"

echo "===== EVAL K_R FULL ====="
python "$python_dir/task.py" \
    --base_model "$base_model" \
    --lora_weights "$checkpoint_dir" \
    --out_dir "$result_dir" \
    --template_dir "$python_dir" \
    --prompt_template llama-qa-template \
    --num_beams=4 \
    --top_k 2 \
    --max_new_tokens=256 \
    --eval_batch_size 2 \
    --path_dataset "$test_retain_kr" \
    2>&1 | tee "$log_dir/eval_kr_full.log"

echo "===== ACCURACY FILES ====="
cat "$result_dir"/trivia_qa/*accuracy.txt

echo
echo "===== DONE ====="
echo "split=$split"
echo "checkpoint_dir=$checkpoint_dir"
echo "result_dir=$result_dir"
echo "log_dir=$log_dir"
