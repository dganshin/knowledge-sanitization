#!/bin/bash

set -euo pipefail

# 公共路径。本脚本预期在远端 Linux GPU 服务器上运行。
python_dir='.'
base_model='/root/autodl-tmp/models/llama-hf/7B'

# 训练和评测参数。
# batch_size 是等效总 batch；micro_batch_size 是每次实际喂给 GPU 的 batch。
# eval_batch_size 控制评测吞吐和显存占用。
batch_size=128
micro_batch_size=8
num_epochs=20
eval_batch_size=4
kr_sample_seed=42
splits="${SPLITS:-1 2 3 4 5 6 7 8 9 10}"
split_label="splits$(echo "$splits" | tr ' ' '_')"
run_id_base="${RUN_ID:-bs${batch_size}_mb${micro_batch_size}_e${num_epochs}_kr1s2000_kr500}"
run_id="${run_id_base}_${split_label}_$(date +%Y%m%d_%H%M%S)"

# 命令行日志会作为纯文本实验记录提交回仓库。
log_root="docs/experiment-command-logs/${run_id}"
mkdir -p "$log_root"
summary_file="${log_root}/summary.md"
global_summary_file="docs/experiment-command-logs/sanitization_split_summary.md"

# 运行单条命令，保存 stdout/stderr，并在每步结束后记录 GPU 状态。
# 每次 train/eval 都是独立 Python 进程；正常情况下进程退出后 CUDA 显存会释放。
# 如果日志里仍有显存残留，通常说明还有外部 Python 进程没有退出。
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

# 写入本轮实验使用的配置和 git commit，方便之后追溯。
echo "===== sanitization selected-split run =====" | tee "${log_root}/run_summary.log"
echo "date: $(date -Is)" | tee -a "${log_root}/run_summary.log"
echo "commit: $(git rev-parse HEAD)" | tee -a "${log_root}/run_summary.log"
echo "base_model: ${base_model}" | tee -a "${log_root}/run_summary.log"
echo "run_id: ${run_id}" | tee -a "${log_root}/run_summary.log"
echo "splits: ${splits}" | tee -a "${log_root}/run_summary.log"
echo "batch_size: ${batch_size}" | tee -a "${log_root}/run_summary.log"
echo "micro_batch_size: ${micro_batch_size}" | tee -a "${log_root}/run_summary.log"
echo "num_epochs: ${num_epochs}" | tee -a "${log_root}/run_summary.log"
echo "eval_batch_size: ${eval_batch_size}" | tee -a "${log_root}/run_summary.log"
echo "kr_sample_seed: ${kr_sample_seed}" | tee -a "${log_root}/run_summary.log"
echo "logs: ${log_root}" | tee -a "${log_root}/run_summary.log"
echo | tee -a "${log_root}/run_summary.log"

{
    echo "# Sanitization split 汇总"
    echo
    echo "本文件由 \`run_sanitization_10splits.sh\` 自动生成。每完成一个 split，会追加该 split 的 K_F / K_S / K_R 结果。"
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
    echo "| batch_size | \`${batch_size}\` |"
    echo "| micro_batch_size | \`${micro_batch_size}\` |"
    echo "| num_epochs | \`${num_epochs}\` |"
    echo "| eval_batch_size | \`${eval_batch_size}\` |"
    echo "| kr_sample_seed | \`${kr_sample_seed}\` |"
    echo "| log_root | \`${log_root}\` |"
    echo
    echo "## 结果表"
    echo
    echo "| Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Notes |"
    echo "|---:|---:|---:|---:|---:|---|"
} > "$summary_file"

expected_global_summary_header="| Date | Commit | Run ID | Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Log dir |"
if [ -f "$global_summary_file" ] && ! grep -Fq "$expected_global_summary_header" "$global_summary_file"; then
    mv "$global_summary_file" "${global_summary_file}.bak_$(date +%Y%m%d_%H%M%S)"
fi

if [ ! -f "$global_summary_file" ]; then
    {
        echo "# Sanitization split 累积汇总"
        echo
        echo "本文件由 \`run_sanitization_10splits.sh\` 增量追加。多次运行不同 \`SPLITS\` 时，结果会继续写入本文件。"
        echo
        echo "| Date | Commit | Run ID | Split | K_F accuracy | K_S accuracy | K_R accuracy | K_R sample size | Log dir |"
        echo "|---|---|---|---:|---:|---:|---:|---:|---|"
    } > "$global_summary_file"
fi

# 逐个 split 执行完整流程：先训练，再立刻评测 K_F/K_S/K_R。
# 这样可以先跑 SPLITS="1 2 3" 观察效果；如果中途发现 bug，可以尽早停止。
for num in ${splits}; do
    lora_path="out/${run_id}/triviaqa_${num}/lora_sanitization"
    train_sanitize="${python_dir}/data/triviaqa_${num}/train_5-forget-answers_85-percent-retain.jsonl"
    out_dir="out/${run_id}/triviaqa_${num}/results"
    test_forget_K_F="${python_dir}/data/triviaqa_${num}/test-forget_gold-answer_K-F"
    test_forget_K_S="${python_dir}/data/triviaqa_${num}/test-forget_sanitization-phrase_K-S"
    test_retain_K_R="${python_dir}/data/triviaqa_${num}/test-retrain_K-R"

    # 1. 训练当前 split 的 LoRA adapter。
    # 输出目录为 out/<run_id>/triviaqa_<split>/lora_sanitization。
    run_and_log "split${num}_train" \
        python "${python_dir}/finetune.py" \
            --base_model "${base_model}" \
            --data_path "${train_sanitize}" \
            --output_dir "${lora_path}" \
            --template_dir "${python_dir}" \
            --load_in_8bit=false \
            --batch_size "${batch_size}" \
            --micro_batch_size "${micro_batch_size}" \
            --num_epochs "${num_epochs}"

    # 2. 全量评测 K_F。
    # K_F 衡量 forget 问题是否仍泄露原答案，越低越好。
    # 这里故意不加 --show，避免输出每条样本的详细内容导致日志过大。
    run_and_log "split${num}_eval_kf" \
        python "${python_dir}/task.py" \
            --base_model "${base_model}" \
            --lora_weights "${lora_path}" \
            --out_dir "${out_dir}" \
            --template_dir "${python_dir}" \
            --eval_batch_size "${eval_batch_size}" \
            --top_k 2 \
            --num_beams=4 \
            --max_new_tokens=256 \
            --path_dataset "${test_forget_K_F}"

    # 3. 全量评测 K_S。
    # K_S 衡量是否严格输出 sanitization phrase: "I don't know."，越高越好。
    run_and_log "split${num}_eval_ks" \
        python "${python_dir}/task.py" \
            --base_model "${base_model}" \
            --lora_weights "${lora_path}" \
            --out_dir "${out_dir}" \
            --template_dir "${python_dir}" \
            --eval_batch_size "${eval_batch_size}" \
            --top_k 2 \
            --num_beams=4 \
            --max_new_tokens=256 \
            --path_dataset "${test_forget_K_S}"

    # 4. 抽样评测 K_R。
    # 每个 split 的 full K_R 约 1.79 万条，调参阶段全量评测成本过高。
    # split 1 抽样 2000 条作为主要 retain 参考；split 2-10 各抽样 500 条节约时间。
    if [ "$num" -eq 1 ]; then
        kr_test_size=2000
    else
        kr_test_size=500
    fi

    run_and_log "split${num}_eval_kr_sample${kr_test_size}" \
        python "${python_dir}/task.py" \
            --base_model "${base_model}" \
            --lora_weights "${lora_path}" \
            --out_dir "${out_dir}" \
            --template_dir "${python_dir}" \
            --eval_batch_size "${eval_batch_size}" \
            --top_k 2 \
            --num_beams=4 \
            --max_new_tokens=256 \
            --path_dataset "${test_retain_K_R}" \
            --test_size "${kr_test_size}" \
            --sample_seed "${kr_sample_seed}"

    kf_accuracy_file="${out_dir}/trivia_qa/TASK-triviaqa_${num}_DATA-test-forget_gold-answer_K-F_MODEL-lora_sanitization_accuracy.txt"
    ks_accuracy_file="${out_dir}/trivia_qa/TASK-triviaqa_${num}_DATA-test-forget_sanitization-phrase_K-S_MODEL-lora_sanitization_accuracy.txt"
    kr_accuracy_file="${out_dir}/trivia_qa/TASK-triviaqa_${num}_DATA-test-retrain_K-R_MODEL-lora_sanitization_accuracy.txt"

    kf_accuracy="$(read_accuracy "$kf_accuracy_file")"
    ks_accuracy="$(read_accuracy "$ks_accuracy_file")"
    kr_accuracy="$(read_accuracy "$kr_accuracy_file")"

    echo "| ${num} | ${kf_accuracy} | ${ks_accuracy} | ${kr_accuracy} | ${kr_test_size} | completed |" | tee -a "$summary_file"
    echo "| $(date -Is) | $(git rev-parse --short HEAD) | ${run_id} | ${num} | ${kf_accuracy} | ${ks_accuracy} | ${kr_accuracy} | ${kr_test_size} | ${log_root} |" >> "$global_summary_file"
done

echo "===== completed =====" | tee -a "${log_root}/run_summary.log"
echo "logs: ${log_root}" | tee -a "${log_root}/run_summary.log"
echo "summary: ${summary_file}" | tee -a "${log_root}/run_summary.log"
echo "global_summary: ${global_summary_file}" | tee -a "${log_root}/run_summary.log"
