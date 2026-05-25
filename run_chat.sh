lora_path="${LORA_PATH:-/root/autodl-tmp/checkpoints/triviaqa_1/lora_sanitization}"

python generate.py \
    --base_model "${BASE_MODEL:-/root/autodl-tmp/models/llama-hf/7B}" \
    --lora_weights $lora_path \
    --top_k 40
