#!/usr/bin/env bash
# One-time install: copy service file, register with systemd, enable + start.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo cp "$SCRIPT_DIR/lego-ball-machine.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lego-ball-machine.service
echo "Installed and started. ./status.sh to check, ./logs.sh to tail."
