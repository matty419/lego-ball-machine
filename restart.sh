#!/usr/bin/env bash
# Restart the service — run after syncing new code.
set -euo pipefail
sudo systemctl restart lego-ball-machine.service
sudo systemctl --no-pager status lego-ball-machine.service | head -n 5
echo
echo "  → http://raspberrypi.local:5000/"
