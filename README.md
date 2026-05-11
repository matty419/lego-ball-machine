# Lego Ball Machine

Phone-controlled Lego ball machine. A small Flask app on a Raspberry Pi drives two continuous-rotation servos and a bank of RGB LEDs via a Pimoroni Inventor HAT Mini — controlled from any browser on the same Wi-Fi.

## Hardware

- Raspberry Pi (tested on Pi 3 Model B+) running Raspberry Pi OS
- [Pimoroni Inventor HAT Mini](https://shop.pimoroni.com/products/inventor-hat-mini)
- 2× [Pimoroni Geekservo Lego-compatible continuous-rotation servos](https://shop.pimoroni.com/products/geekservo-lego-compatible-continuous-rotation-servo)
- A Lego ball machine to plug it all into

Wire each servo to a 3-pin SERVOS header (we use `SERVO_1` and `SERVO_2`). Yellow = signal, red = V+, brown = GND.

## What the UI does

Per motor:
- **Start / Stop** — turn the motor on (current direction & speed) or off
- **Run 5 seconds** — auto-stops after 5 seconds
- **Reverse** — flip direction; applies immediately if the motor's already spinning
- **Speed** — 4-stop slider (Slow / Medium / Fast / Max), default Medium

Plus three LED test buttons (on / off / 10-second rainbow pattern). The 8 onboard RGB LEDs split between the motors — first half green while motor 1 runs forward (red in reverse), second half tracks motor 2.

## Setup

```bash
sudo raspi-config nonint do_i2c 0
sudo apt install -y python3-pip
sudo python3 -m pip install --upgrade pip setuptools wheel
sudo pip install --ignore-installed --upgrade inventorhatmini flask gpiodevice
cd ~/lego-ball-machine
sudo python3 app.py
```

Then open `http://<pi-ip>:5000` (or `http://raspberrypi.local:5000`) on your phone.

## Run at boot

Helper scripts wrap the systemd commands:

| Script | Runs on | What it does |
| --- | --- | --- |
| `./sync.sh`    | Mac | Rsync the project to the Pi. |
| `./install.sh` | Pi  | Register the systemd service and start it. One-time. |
| `./restart.sh` | Pi  | Restart after syncing new code. |
| `./logs.sh`    | Pi  | Follow the service logs. |
| `./status.sh`  | Pi  | Service status. |
| `./stop.sh`    | Pi  | Stop the service. |

## Project layout

```
app.py                       # Flask server, motor + LED control
templates/index.html         # Phone UI
test_servo.py                # Direct hardware check, bypasses Flask
lego-ball-machine.service    # systemd unit
*.sh                         # convenience scripts
CLAUDE.md                    # in-depth notes (API, gotchas, etc.)
```

See [CLAUDE.md](CLAUDE.md) for hardware-specific gotchas (e.g. `value()` vs `to_max/to_min` on the Geekservo + inventorhatmini 1.0.0 combo) and detailed endpoint docs.
