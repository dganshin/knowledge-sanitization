#!/bin/bash

set -euo pipefail

if [ -z "${TMUX:-}" ] && [ -z "${STY:-}" ] && [ "${ALLOW_NO_TMUX:-false}" != "true" ]; then
    echo "Please start tmux first: tmux new -s ks_run"
    echo "If you really want to run without tmux/screen, use ALLOW_NO_TMUX=true"
    exit 1
fi

echo "Step 1/3: checking proxy service"
if ! pgrep -f "mihomo" >/dev/null 2>&1; then
    echo "Warning: mihomo/clash does not seem to be running."
fi

echo "Step 2/3: running Orig baseline"
bash "$(dirname "$0")/run_orig_baseline.sh"

echo "Step 3/3: running sanitization nightly"
bash "$(dirname "$0")/run_sanitization_nightly.sh"
