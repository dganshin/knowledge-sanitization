#!/bin/bash

set -euo pipefail

# Orig baseline: 原始 LLaMA-7B，不训练、不加载 LoRA，只做评测。
# 可通过环境变量覆盖，例如：
# SPLITS="1" KR_SAMPLE_SIZE=500 bash run_orig_baseline_splits.sh

python_dir='.'
base_model="${BASE_MODEL:-/root/autodl-tmp/models/llama-hf/7B}"
splits="${SPLITS:-1 2 3 4 5 6 7 8 9 10}"
eval_batch_size="${EVAL_BATCH_SIZE:-4}"
kr_sample_size="${KR_SAMPLE_SIZE:-500}"
kr_sample_seed="${KR_SAMPLE_SEED:-42}"
run_kr="${RUN_KR:-true}"

run_id="orig_baseline_$(date +%Y%m%d_%H%M%S)"
log_root="docs/experiment-command-logs/${run_id}"
mkdir -p "$log_root"
summary_file="${log_root}/summary.md"
global_summary_file="docs/experiment-command-logs/orig_baseline_summary.md"

run_and_log() {
    local name="$1"
    local log_file="${log_root}/${name}.log"
    shift

    echo "===== ${name} ====="
    echo "command: $*"
    echo

    "$@" 2>&1 | tee "${log_file}"

    {
        echo
        echo "===== GPU state after ${name} ====="
        if command -v nvidia-smi >/dev/null 2>&1; then
            nvidia-smi
        else
            echo "nvidia-smi not found"
        fi
    } | tee -a "${log_file}" "${log_root}/gpu_state.log" >/dev/null
}

read_accuracy() {
    local accuracy_file="$1"

    if [ -f "$accuracy_file" ]; then
        sed 's/^accuracy: //' "$accuracy_file"
    else
        echo "missing"
    fi
}

is_true() {
    case "${1,,}" in
        1|true|yes|y|on) return 0 ;;
        *) return 1 ;;
    esac
}

echo "===== orig baseline run =====" | tee "${log_root}/run_summary.log"
echo "date: $(date -Is)" | tee -a "${log_root}/run_summary.log"
echo "commit: $(git rev-parse HEAD)" | tee -a "${log_root}/run_summary.log"
echo "base_model: ${base_model}" | tee -a "${log_root}/run_summary.log"
echo "run_id: ${run_id}" | tee -a "${log_root}/run_summary.log"
echo "splits: ${splits}" | tee -a "${log_root}/run_summary.log"
echo "eval_batch_size: ${eval_batch_size}" | tee -a "${log_root}/run_summary.log"
echo "kr_sample_size: ${kr_sample_size}" | tee -a "${log_root}/run_summary.log"
echo "kr_sample_seed: ${kr_sample_seed}" | tee -a "${log_root}/run_summary.log"
echo "run_kr: ${run_kr}" | tee -a "${log_root}/run_summary.log"
echo "logs: ${log_root}" | tee -a "${log_root}/run_summary.log"
echo | tee -a "${log_root}/run_summary.log"

{
    echo "# Orig baseline split 汇总"
    echo
    echo "本文件由 \`run_orig_baseline_splits.sh\` 自动生成。Orig baseline 不训练、不加载 LoRA。"
    echo
    echo "## 运行配置"
    echo
    echo "| 字段 | 值 |"
    echo "|---|---|"
    echo "| date | \`$(date -Is)\` |"
    echo "| commit | \`$(git rev-parse HEAD)\` |"
    echo "| base_model | \`${base_model}\` |"
    echo "| run_id | \`${run_id}\` |"
    echo "| splits | \`${splits}\` |"
    echo "| eval_batch_size | \`${eval_batch_size}\` |"
    echo "| kr_sample_size | \`${kr_sample_size}\` |"
    echo "| kr_sample_seed | \`${kr_sample_seed}\` |"
    echo "| run_kr | \`${run_kr}\` |"
    echo "| log_root | \`${log_root}\` |"
    echo
    echo "## 结果表"
    echo
    echo "| Split | Orig K_F accuracy | Orig K_S accuracy | Orig K_R sample accuracy | K_R sample size | Notes |"
    echo "|---:|---:|---:|---:|---:|---|"
} > "$summary_file"

if [ ! -f "$global_summary_file" ]; then
    {
        echo "# Orig baseline 累积汇总"
        echo
        echo "本文件由 \`run_orig_baseline_splits.sh\` 增量追加。"
        echo
        echo "| Date | Commit | Run ID | Split | Orig K_F accuracy | Orig K_S accuracy | Orig K_R sample accuracy | K_R sample size | Log dir |"
        echo "|---|---|---|---:|---:|---:|---:|---:|---|"
    } > "$global_summary_file"
fi

for num in ${splits}; do
    out_dir="out/orig/triviaqa_${num}/results"
    test_forget_K_F="${python_dir}/data/triviaqa_${num}/test-forget_gold-answer_K-F"
    test_forget_K_S="${python_dir}/data/triviaqa_${num}/test-forget_sanitization-phrase_K-S"
    test_retain_K_R="${python_dir}/data/triviaqa_${num}/test-retrain_K-R"

    run_and_log "split${num}_orig_eval_kf" \
        python "${python_dir}/task.py" \
            --base_model "${base_model}" \
            --lora_weights no-lora \
            --no_peft \
            --out_dir "${out_dir}" \
            --template_dir "${python_dir}" \
            --eval_batch_size "${eval_batch_size}" \
            --top_k 2 \
            --num_beams=4 \
            --max_new_tokens=256 \
            --path_dataset "${test_forget_K_F}"

    run_and_log "split${num}_orig_eval_ks" \
        python "${python_dir}/task.py" \
            --base_model "${base_model}" \
            --lora_weights no-lora \
            --no_peft \
            --out_dir "${out_dir}" \
            --template_dir "${python_dir}" \
            --eval_batch_size "${eval_batch_size}" \
            --top_k 2 \
            --num_beams=4 \
            --max_new_tokens=256 \
            --path_dataset "${test_forget_K_S}"

    kr_accuracy="skipped"
    kr_size="0"
    if is_true "$run_kr"; then
        run_and_log "split${num}_orig_eval_kr_sample${kr_sample_size}" \
            python "${python_dir}/task.py" \
                --base_model "${base_model}" \
                --lora_weights no-lora \
                --no_peft \
                --out_dir "${out_dir}" \
                --template_dir "${python_dir}" \
                --eval_batch_size "${eval_batch_size}" \
                --top_k 2 \
                --num_beams=4 \
                --max_new_tokens=256 \
                --path_dataset "${test_retain_K_R}" \
                --test_size "${kr_sample_size}" \
                --sample_seed "${kr_sample_seed}"

        kr_accuracy_file="${out_dir}/trivia_qa/TASK-triviaqa_${num}_DATA-test-retrain_K-R_MODEL-no-lora_accuracy.txt"
        kr_accuracy="$(read_accuracy "$kr_accuracy_file")"
        kr_size="${kr_sample_size}"
    fi

    kf_accuracy_file="${out_dir}/trivia_qa/TASK-triviaqa_${num}_DATA-test-forget_gold-answer_K-F_MODEL-no-lora_accuracy.txt"
    ks_accuracy_file="${out_dir}/trivia_qa/TASK-triviaqa_${num}_DATA-test-forget_sanitization-phrase_K-S_MODEL-no-lora_accuracy.txt"

    kf_accuracy="$(read_accuracy "$kf_accuracy_file")"
    ks_accuracy="$(read_accuracy "$ks_accuracy_file")"

    echo "| ${num} | ${kf_accuracy} | ${ks_accuracy} | ${kr_accuracy} | ${kr_size} | completed |" | tee -a "$summary_file"
    echo "| $(date -Is) | $(git rev-parse --short HEAD) | ${run_id} | ${num} | ${kf_accuracy} | ${ks_accuracy} | ${kr_accuracy} | ${kr_size} | ${log_root} |" >> "$global_summary_file"
done

echo "===== completed =====" | tee -a "${log_root}/run_summary.log"
echo "logs: ${log_root}" | tee -a "${log_root}/run_summary.log"
echo "summary: ${summary_file}" | tee -a "${log_root}/run_summary.log"
echo "global_summary: ${global_summary_file}" | tee -a "${log_root}/run_summary.log"
