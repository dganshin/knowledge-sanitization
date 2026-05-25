#!/bin/bash

set -euo pipefail

bash "$(dirname "$0")/run_sanitization_job.sh" "$@"
