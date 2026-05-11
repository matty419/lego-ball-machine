#!/usr/bin/env bash
# Show service status (running? last logs?).
exec sudo systemctl --no-pager status lego-ball-machine.service
