#!/bin/bash

set -euo pipefail

python_dir='.'
base_model='/root/autodl-tmp/models/llama-hf/7B'

num=1
out_dir="/root/autodl-tmp/outputs_clean_7214e4d/triviaqa_${num}/results"
lora_path="/root/autodl-tmp/checkpoints_clean_7214e4d/triviaqa_${num}/lora_sanitization"

train_sanitize="${python_dir}/data/triviaqa_${num}/train_5-forget-answers_85-percent-retain.jsonl"
test_forget_K_F="${python_dir}/data/triviaqa_${num}/test-forget_gold-answer_K-F"
test_forget_K_S="${python_dir}/data/triviaqa_${num}/test-forget_sanitization-phrase_K-S"
test_retain_K_R="${python_dir}/data/triviaqa_${num}/test-retrain_K-R"

log_dir="/root/autodl-tmp/outputs_clean_7214e4d/triviaqa_${num}/logs"
mkdir -p "$log_dir"

echo "===== REPRO 7214e4d MINIMAL SPLIT ${num} ====="
echo "commit: $(git rev-parse HEAD)"
echo "base_model: $base_model"
echo "train_sanitize: $train_sanitize"
echo "out_dir: $out_dir"
echo "lora_path: $lora_path"
echo "batch_size: 128"
echo "micro_batch_size: 1"
echo "num_epochs: 20"
echo "NOTE: load_in_8bit=false is an environment compatibility compromise."
echo "NOTE: micro_batch_size=1 is a 24G hardware compromise from original script micro_batch_size=128."
echo "NOTE: prompt, LoRA target_modules, loss, eval sets, and max_length semantics are unchanged from 7214e4d."
echo

python $python_dir/finetune.py \
    --base_model $base_model \
    --data_path $train_sanitize \
    --output_dir $lora_path \
    --template_dir $python_dir \
    --load_in_8bit=false \
    --batch_size 128 \
    --micro_batch_size 1 \
    --num_epochs 20 \
    2>&1 | tee "$log_dir/train.log"

echo "===== adapter_config ====="
cat "$lora_path/adapter_config.json" | tee "$log_dir/adapter_config.json"

python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights $lora_path \
    --out_dir $out_dir \
    --template_dir $python_dir \
    --eval_batch_size 2 \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_forget_K_F \
    2>&1 | tee "$log_dir/eval_kf.log"

python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights $lora_path \
    --out_dir $out_dir \
    --template_dir $python_dir \
    --eval_batch_size 2 \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_forget_K_S \
    2>&1 | tee "$log_dir/eval_ks.log"

python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights $lora_path \
    --out_dir $out_dir \
    --template_dir $python_dir \
    --eval_batch_size 2 \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_retain_K_R \
    2>&1 | tee "$log_dir/eval_kr_full.log"

echo "===== accuracy ====="
cat "$out_dir"/trivia_qa/*accuracy.txt | tee "$log_dir/accuracy_all.txt"
