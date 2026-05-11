#!/usr/bin/env bash
# Sync project files from this Mac to the Pi.
# After this, run ./restart.sh on the Pi to pick up new code.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rsync -av --exclude='.git' --exclude='.venv' \
  "$SCRIPT_DIR/" matt@raspberrypi.local:~/lego-ball-machine/
