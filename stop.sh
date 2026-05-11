#!/usr/bin/env bash
# Stop the service. Boot-start remains enabled — use `sudo systemctl
# disable lego-ball-machine` to also stop it starting at boot.
set -euo pipefail
sudo systemctl stop lego-ball-machine.service
echo "Stopped. ./restart.sh to bring it back."
