#!/bin/bash

set -euo pipefail

python_dir="${PYTHON_DIR:-.}"
base_model="${BASE_MODEL:-/root/autodl-tmp/models/llama-hf/7B}"

num="${TRIVIAQA_SPLIT:-1}" # 1 ~ 10
out_root="${OUT_ROOT:-/root/autodl-tmp/outputs}"
checkpoint_root="${CHECKPOINT_ROOT:-/root/autodl-tmp/checkpoints}"
out_dir="${out_root}/triviaqa_${num}/results"
lora_path="${checkpoint_root}/triviaqa_${num}/lora_sanitization"

train_sanitize="${python_dir}/data/triviaqa_${num}/train_5-forget-answers_85-percent-retain.jsonl"
test_forget_K_F="${python_dir}/data/triviaqa_${num}/test-forget_gold-answer_K-F"
test_forget_K_S="${python_dir}/data/triviaqa_${num}/test-forget_sanitization-phrase_K-S"
test_retain_K_R="${python_dir}/data/triviaqa_${num}/test-retrain_K-R"
batch_size="${BATCH_SIZE:-8}"
micro_batch_size="${MICRO_BATCH_SIZE:-1}"
num_epochs="${NUM_EPOCHS:-1}"
load_in_8bit="${LOAD_IN_8BIT:-false}"

# Sanitization tuning
python $python_dir/finetune.py \
    --base_model $base_model \
    --data_path $train_sanitize \
    --output_dir $lora_path \
    --template_dir $python_dir \
    --load_in_8bit=$load_in_8bit \
    --batch_size $batch_size \
    --micro_batch_size $micro_batch_size \
    --num_epochs $num_epochs

if [ ! -f "$lora_path/adapter_config.json" ]; then
    echo "Missing LoRA adapter output: $lora_path/adapter_config.json"
    exit 1
fi

# Evaluation on K_F
python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights $lora_path \
    --out_dir $out_dir  \
    --template_dir $python_dir \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_forget_K_F  \
    --show  


# Evaluation on K_S
python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights $lora_path \
    --out_dir $out_dir  \
    --template_dir $python_dir \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_forget_K_S  \
    --show  


# Evaluation on K_R
python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights $lora_path \
    --out_dir $out_dir  \
    --template_dir $python_dir \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_retain_K_R  \
    --show  
