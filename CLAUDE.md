# Lego Ball Machine

A small Flask web app running on a Raspberry Pi to drive a Lego ball machine via a Pimoroni Inventor HAT Mini. Phone-controlled over local Wi-Fi: per-motor Start, Stop, Run-for-5-seconds, Reverse — plus onboard LED test controls.

## Hardware

- **Pi**: Raspberry Pi 3 Model B+
- **HAT**: [Pimoroni Inventor HAT Mini](https://shop.pimoroni.com/products/inventor-hat-mini) — 2× motor outs (DRV8833), 4× servo, 1× user button, 2× onboard RGB LEDs
- **Drive**: two [Pimoroni Geekservo Lego-compatible continuous-rotation servos](https://shop.pimoroni.com/products/geekservo-lego-compatible-continuous-rotation-servo) — 3-wire each (Red=V+, Brown=GND, Yellow=Signal), 3.3-6V, PWM-driven. Plugged into `SERVO_1` and `SERVO_2` (3-pin headers), yellow wire on top SIG pin.
- 8 onboard RGB LEDs split between the motors: first half (0-3) tracks motor 1, second half (4-7) tracks motor 2. Each half is **green** when its motor is running forward, **red** when running reverse, off when idle. Manual `/api/leds/*` endpoints override both halves until the next motor state change.

## Stack

- Python 3, Flask (`host=0.0.0.0`, `port=5000`, `threaded=True`)
- `inventorhatmini` Python library (Pimoroni)
- No frontend framework — single static `templates/index.html` with vanilla JS

## Layout

```
app.py                  # Flask server + motor/LED control
templates/index.html    # phone UI (3 buttons + status)
requirements.txt        # flask, inventorhatmini
```

## Endpoints

- `GET  /`                              — UI
- `POST /api/motors/<id>/start`         — motor on, current direction & speed (`<id>` is `1` or `2`)
- `POST /api/motors/<id>/stop`          — motor off
- `POST /api/motors/<id>/run5`          — motor on, auto-stop after 5 s
- `POST /api/motors/<id>/reverse`       — flip direction; if running, applies immediately
- `POST /api/motors/<id>/speed/<level>` — set speed (`level` ∈ 0..3); if running, applies immediately
- `POST /api/leds/on`                   — solid white at 50% brightness
- `POST /api/leds/off`                  — clear LEDs
- `POST /api/leds/pattern`              — 10-second rainbow cycle, then clear
- `GET  /api/status`                    — `{motors: {"1": {running, direction, speed}, "2": {…}}}`; UI polls every 1 s

Speed is a discrete level 0-3 (Slow / Medium / Fast / Max). It maps to a pulse-width offset from the 1500µs centre (±200 / ±400 / ±600 / ±1000 µs). Direction sets the sign, so speed and direction are orthogonal — flipping Reverse keeps the current speed level.

Mutating motor endpoints return the full motor-state snapshot (same shape as `/api/status`).

Generation counters:
- `Motor.generation` (per-motor) — bumped by that motor's ops *except* `/reverse` and `/speed`. The 5-second timer captures it at start and only stops if it hasn't moved — so Start / Run-5 / Stop on the *same* motor cancel that motor's pending timed stop. Reverse and speed changes mid-Run-5 leave the auto-stop intact. Motors are independent: a Run-5 on motor 1 isn't affected by anything done to motor 2.
- `led_generation` — bumped by every LED-touching op (manual on/off, pattern start, any motor state change). The pattern thread checks it each frame and bails if anything else has taken over the LEDs.

## Inventor HAT Mini API (confirmed against examples)

```python
from inventorhatmini import InventorHATMini, SERVO_1, NUM_LEDS

board = InventorHATMini()
servo = board.servos[SERVO_1]   # SERVO_1..SERVO_4 — 3-pin headers
servo.enable()
servo.to_max()      # full forward — empirically works on the Geekservo
servo.to_min()      # full reverse
servo.to_mid()      # stop (centre pulse)
servo.disable()
```

> **Gotcha:** `servo.value(1.0)` / `value(-1.0)` *don't* drive this Geekservo at all on `inventorhatmini` 1.0.0 — the default calibration maps them to pulse widths that fall inside the servo's deadband. Use the positional `to_max/to_min/to_mid` (or direct `pulse(us)`) instead. Confirmed by `test_servo.py` output.

```python
board.leds.set_hsv(i, hue, sat, val)   # i in range(NUM_LEDS); also set_rgb in the underlying Plasma lib
board.leds.show()
board.leds.clear()

board.switch_pressed()   # only ONE user button exists ("User"), not A/B
```

(For DC motors via the H-bridge outputs, the API is `board.motors[MOTOR_A]` with `full_positive()`, `full_negative()`, `stop()`, `coast()`, `speed(-1.0..1.0)`. Not used here.)

## Pi setup

This Pi is single-purpose, so we install everything system-wide — no venv.

```bash
sudo raspi-config nonint do_i2c 0          # enable I2C
sudo apt install -y python3-pip
sudo python3 -m pip install --upgrade pip setuptools wheel
sudo pip install --ignore-installed --upgrade inventorhatmini flask gpiodevice
cd ~/lego-ball-machine
sudo python3 app.py
```

Notes:
- The system pip from apt is too old to parse modern `pyproject.toml` — upgrading pip first is mandatory.
- `--ignore-installed` is needed because the apt-installed `python3-blinker` (a Flask 1.x dep) blocks pip's upgrade. The newer pip install in `/usr/local/lib` shadows it.
- `gpiodevice` has to be named explicitly: `inventorhatmini` 1.0.0 uses it but doesn't declare it in its package metadata.
- `sudo` to run is required — the WS281x LEDs use DMA/PWM and need `/dev/mem` access. If you'd rather drop root, instantiate `InventorHATMini(init_leds=False)` and remove the LED calls.

Then visit `http://<pi-ip>:5000` from a phone on the same Wi-Fi (`hostname -I` on the Pi for the IP).

## Sync from Mac to Pi

```bash
./sync.sh
```

Wraps `rsync -av --exclude='.git' --exclude='.venv' ./ matt@raspberrypi.local:~/lego-ball-machine/`. User on the Pi is `matt` (not the default `pi`). `rsync -a` preserves the executable bit on `*.sh` scripts. After syncing, run `./restart.sh` on the Pi to pick up new code.

## Run at boot (systemd)

A unit file [`lego-ball-machine.service`](lego-ball-machine.service) is included plus convenience scripts in the project root:

| Script | Runs on | What it does |
| --- | --- | --- |
| `./sync.sh`    | Mac | Rsync the project to the Pi. |
| `./install.sh` | Pi  | Copy unit file, register with systemd, enable + start. One-time setup. |
| `./restart.sh` | Pi  | Restart the service after syncing new code. |
| `./logs.sh`    | Pi  | Tail live logs from the service. Ctrl-C to exit. |
| `./status.sh`  | Pi  | Show service status. |
| `./stop.sh`    | Pi  | Stop the service (boot-start remains enabled). |

## Status as of last session (2026-05-09)

- Repo scaffolded on the Mac at `/Users/matt/Coding/lego-ball-machine`
- `git init` done, files staged, **no commit yet**
- Nothing tested on the Pi yet — first run will be the smoke test
- Hardware is in hand
