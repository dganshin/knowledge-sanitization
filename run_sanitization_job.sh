#!/bin/bash

set -euo pipefail

if [ -z "${TMUX:-}" ] && [ -z "${STY:-}" ] && [ "${ALLOW_NO_TMUX:-false}" != "true" ]; then
    echo "Please start tmux first: tmux new -s ks_run"
    echo "If you really want to run without tmux/screen, use ALLOW_NO_TMUX=true"
    exit 1
fi

if ! pgrep -f "mihomo" >/dev/null 2>&1; then
    echo "Warning: mihomo/clash does not seem to be running."
fi

gpu_tier="${GPU_TIER:-24g}"
split="${TRIVIAQA_SPLIT:-1}"
shutdown_on_success="${SHUTDOWN_ON_SUCCESS:-false}"

case "$gpu_tier" in
    24g)
        : "${BATCH_SIZE:=24}"
        : "${MICRO_BATCH_SIZE:=3}"
        : "${NUM_EPOCHS:=3}"
        : "${PREPROCESS_NUM_PROC:=8}"
        : "${DATALOADER_NUM_WORKERS:=8}"
        : "${EVAL_BATCH_SIZE:=2}"
        ;;
    48g|40g)
        : "${BATCH_SIZE:=32}"
        : "${MICRO_BATCH_SIZE:=4}"
        : "${NUM_EPOCHS:=3}"
        : "${PREPROCESS_NUM_PROC:=8}"
        : "${DATALOADER_NUM_WORKERS:=8}"
        : "${EVAL_BATCH_SIZE:=8}"
        ;;
    80g)
        : "${BATCH_SIZE:=64}"
        : "${MICRO_BATCH_SIZE:=8}"
        : "${NUM_EPOCHS:=3}"
        : "${PREPROCESS_NUM_PROC:=8}"
        : "${DATALOADER_NUM_WORKERS:=8}"
        : "${EVAL_BATCH_SIZE:=16}"
        ;;
    *)
        echo "Unknown GPU_TIER: $gpu_tier"
        echo "Use one of: 24g, 40g, 48g, 80g"
        exit 1
        ;;
esac

export LOAD_IN_8BIT="${LOAD_IN_8BIT:-false}"
export SHOW_EVAL="${SHOW_EVAL:-false}"
export EXPORT_TEXT_RESULTS="${EXPORT_TEXT_RESULTS:-true}"
export TRIVIAQA_SPLIT="$split"
export BATCH_SIZE MICRO_BATCH_SIZE NUM_EPOCHS PREPROCESS_NUM_PROC DATALOADER_NUM_WORKERS EVAL_BATCH_SIZE

echo "Run config:"
echo "  GPU_TIER=$gpu_tier"
echo "  TRIVIAQA_SPLIT=$TRIVIAQA_SPLIT"
echo "  LOAD_IN_8BIT=$LOAD_IN_8BIT"
echo "  BATCH_SIZE=$BATCH_SIZE"
echo "  MICRO_BATCH_SIZE=$MICRO_BATCH_SIZE"
echo "  NUM_EPOCHS=$NUM_EPOCHS"
echo "  PREPROCESS_NUM_PROC=$PREPROCESS_NUM_PROC"
echo "  DATALOADER_NUM_WORKERS=$DATALOADER_NUM_WORKERS"
echo "  EVAL_BATCH_SIZE=$EVAL_BATCH_SIZE"
echo "  SHOW_EVAL=$SHOW_EVAL"
echo "  EXPORT_TEXT_RESULTS=$EXPORT_TEXT_RESULTS"

bash "$(dirname "$0")/run_sanitization.sh"

if [ "$shutdown_on_success" = "true" ]; then
    echo "Run finished successfully. Powering off."
    poweroff
fi
