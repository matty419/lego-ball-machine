#!/usr/bin/env bash
# Tail live logs from the service (Flask stdout/stderr). Ctrl-C to exit.
exec sudo journalctl -u lego-ball-machine.service -f
