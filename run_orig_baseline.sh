#!/bin/bash

set -euo pipefail

python_dir="${PYTHON_DIR:-.}"
base_model="${BASE_MODEL:-/root/autodl-tmp/models/llama-hf/7B}"
num="${TRIVIAQA_SPLIT:-1}"
out_root="${OUT_ROOT:-/root/autodl-tmp/outputs}"
out_dir="${out_root}/triviaqa_${num}/orig_results"
export_tag="${EXPORT_TAG:-triviaqa_${num}_orig}"
show_eval="${SHOW_EVAL:-false}"
eval_batch_size="${EVAL_BATCH_SIZE:-16}"

test_forget_K_F="${python_dir}/data/triviaqa_${num}/test-forget_gold-answer_K-F"
test_forget_K_S="${python_dir}/data/triviaqa_${num}/test-forget_sanitization-phrase_K-S"
test_retain_K_R="${python_dir}/data/triviaqa_${num}/test-retrain_K-R"

show_eval_args=()
if [ "$show_eval" = "true" ]; then
    show_eval_args+=(--show)
fi

python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights no-lora \
    --no_peft \
    --out_dir $out_dir \
    --template_dir $python_dir \
    --eval_batch_size $eval_batch_size \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_forget_K_F \
    "${show_eval_args[@]}"

python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights no-lora \
    --no_peft \
    --out_dir $out_dir \
    --template_dir $python_dir \
    --eval_batch_size $eval_batch_size \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_forget_K_S \
    "${show_eval_args[@]}"

python $python_dir/task.py \
    --base_model $base_model \
    --lora_weights no-lora \
    --no_peft \
    --out_dir $out_dir \
    --template_dir $python_dir \
    --eval_batch_size $eval_batch_size \
    --top_k 2 \
    --num_beams=4 \
    --max_new_tokens=256 \
    --path_dataset $test_retain_K_R \
    "${show_eval_args[@]}"

python $python_dir/scripts/export_text_results.py \
    --repo_dir "$python_dir" \
    --out_dir "$out_dir" \
    --checkpoint_dir "$python_dir" \
    --split "$num" \
    --export_tag "$export_tag"
