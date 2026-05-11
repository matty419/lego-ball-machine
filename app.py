import threading
import time
from dataclasses import dataclass
from typing import Optional

from flask import Flask, jsonify, render_template
from inventorhatmini import NUM_LEDS, SERVO_1, SERVO_2, InventorHATMini

app = Flask(__name__)

# Two Pimoroni Geekservo continuous-rotation servos. 3-wire (Yellow=SIG,
# Red=V+, Brown=GND), plugged into SERVO_1 and SERVO_2 headers.
board = InventorHATMini()


# Pulse-width offset from the 1500us centre per speed level (0-3).
# 1500us is stop; 500us / 2500us are the calibrated extremes.
SPEED_OFFSET_US = {0: 200, 1: 400, 2: 600, 3: 1000}
DEFAULT_SPEED = 1  # Medium


@dataclass
class Motor:
    servo: object
    running: bool = False
    direction: int = 1  # +1 forward, -1 reverse
    speed_level: int = DEFAULT_SPEED  # index into SPEED_OFFSET_US
    # Bumped on every state change *except* /reverse and /speed. The
    # 5-second timer captures it at start and only stops if the
    # generation hasn't moved.
    generation: int = 0


motors = {
    1: Motor(board.servos[SERVO_1]),
    2: Motor(board.servos[SERVO_2]),
}
for m in motors.values():
    m.servo.enable()

state_lock = threading.Lock()
# Shared LED ownership counter. Bumped by every LED-touching op (manual
# on/off, pattern start, motor state changes).
led_generation = 0


def _bump_led_gen_locked() -> None:
    global led_generation
    led_generation += 1


def _set_leds_locked() -> None:
    # LEDs split between motors: motor 1 -> first half of the chain,
    # motor 2 -> second half. Each half is green when its motor is
    # running forward, red when running reverse, off when stopped.
    # Manual /api/leds/* endpoints override until the next motor state
    # change repaints both halves.
    _bump_led_gen_locked()
    board.leds.clear()
    half = NUM_LEDS // 2
    for idx, motor in motors.items():
        if motor.running:
            hue = 0.33 if motor.direction > 0 else 0.0  # green / red
            start = (idx - 1) * half
            for i in range(start, start + half):
                board.leds.set_hsv(i, hue, 1.0, 0.5)
    board.leds.show()


def _apply_direction_locked(motor: Motor) -> None:
    # Direct pulse() — value(±1.0) lands inside the Geekservo's deadband
    # on inventorhatmini v1.0.0 and doesn't move it. pulse() works at
    # every width we've tested (confirmed via test_servo.py).
    offset = SPEED_OFFSET_US[motor.speed_level]
    motor.servo.pulse(1500 + motor.direction * offset)


def _start_motor_locked(motor: Motor) -> None:
    _apply_direction_locked(motor)
    motor.running = True
    _set_leds_locked()


def _stop_motor_locked(motor: Motor) -> None:
    motor.servo.to_mid()
    motor.running = False
    _set_leds_locked()


def _motor_state_locked() -> dict:
    return {
        str(idx): {
            "running": m.running,
            "direction": m.direction,
            "speed": m.speed_level,
        }
        for idx, m in motors.items()
    }


def _get_motor(idx: int) -> Optional[Motor]:
    return motors.get(idx)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/motors/<int:idx>/start")
def api_motor_start(idx):
    motor = _get_motor(idx)
    if motor is None:
        return jsonify(error=f"unknown motor {idx}"), 404
    with state_lock:
        motor.generation += 1
        _start_motor_locked(motor)
        return jsonify(motors=_motor_state_locked())


@app.post("/api/motors/<int:idx>/stop")
def api_motor_stop(idx):
    motor = _get_motor(idx)
    if motor is None:
        return jsonify(error=f"unknown motor {idx}"), 404
    with state_lock:
        motor.generation += 1
        _stop_motor_locked(motor)
        return jsonify(motors=_motor_state_locked())


@app.post("/api/motors/<int:idx>/run5")
def api_motor_run5(idx):
    motor = _get_motor(idx)
    if motor is None:
        return jsonify(error=f"unknown motor {idx}"), 404
    with state_lock:
        motor.generation += 1
        my_gen = motor.generation
        _start_motor_locked(motor)
        snapshot = _motor_state_locked()

    def timed_stop():
        time.sleep(5.0)
        with state_lock:
            if motor.generation == my_gen:
                _stop_motor_locked(motor)

    threading.Thread(target=timed_stop, daemon=True).start()
    return jsonify(motors=snapshot, duration=5)


@app.post("/api/motors/<int:idx>/reverse")
def api_motor_reverse(idx):
    motor = _get_motor(idx)
    if motor is None:
        return jsonify(error=f"unknown motor {idx}"), 404
    with state_lock:
        motor.direction = -motor.direction
        if motor.running:
            _apply_direction_locked(motor)
            _set_leds_locked()  # refresh colour for the new direction
        return jsonify(motors=_motor_state_locked())


@app.post("/api/motors/<int:idx>/speed/<int:level>")
def api_motor_speed(idx, level):
    motor = _get_motor(idx)
    if motor is None:
        return jsonify(error=f"unknown motor {idx}"), 404
    if level not in SPEED_OFFSET_US:
        return jsonify(error=f"invalid speed level {level}"), 400
    with state_lock:
        motor.speed_level = level
        if motor.running:
            _apply_direction_locked(motor)
        return jsonify(motors=_motor_state_locked())


@app.post("/api/leds/on")
def api_leds_on():
    with state_lock:
        _bump_led_gen_locked()
        for i in range(NUM_LEDS):
            board.leds.set_hsv(i, 0.0, 0.0, 0.5)  # white at 50%
        board.leds.show()
    return jsonify(leds="on")


@app.post("/api/leds/off")
def api_leds_off():
    with state_lock:
        _bump_led_gen_locked()
        board.leds.clear()
        board.leds.show()
    return jsonify(leds="off")


@app.post("/api/leds/pattern")
def api_leds_pattern():
    with state_lock:
        _bump_led_gen_locked()
        my_gen = led_generation

    def pattern():
        end_time = time.time() + 10.0
        hue = 0.0
        while time.time() < end_time:
            with state_lock:
                if led_generation != my_gen:
                    return
                for i in range(NUM_LEDS):
                    board.leds.set_hsv(i, (hue + i / NUM_LEDS) % 1.0, 1.0, 0.5)
                board.leds.show()
            hue = (hue + 0.02) % 1.0
            time.sleep(0.05)
        with state_lock:
            if led_generation == my_gen:
                board.leds.clear()
                board.leds.show()

    threading.Thread(target=pattern, daemon=True).start()
    return jsonify(leds="pattern", duration=10)


@app.get("/api/status")
def api_status():
    with state_lock:
        return jsonify(motors=_motor_state_locked())


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True)
    finally:
        with state_lock:
            for motor in motors.values():
                _stop_motor_locked(motor)
                motor.servo.disable()
        board.leds.clear()
        board.leds.show()
