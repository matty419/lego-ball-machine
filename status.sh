#!/usr/bin/env bash
# Show service status (running? last logs?).
sudo systemctl --no-pager status lego-ball-machine.service
echo
echo "  → http://raspberrypi.local:5000/"
