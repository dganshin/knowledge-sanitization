#!/usr/bin/env bash

set -euo pipefail

for split in 1 2 3 4 5; do
    echo "===== RUNNING PAPER SANITIZATION SPLIT ${split} ====="
    SPLIT="$split" bash "$(dirname "$0")/run_paper_sanitization_split.sh"
done
