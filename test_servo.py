"""Variable-speed motor test.

Forward / reverse speeds via direct pulse-width control:
  1500us  — stop (centre pulse)
  >1500us — forward (higher = faster)
  <1500us — reverse (lower = faster)

Inventorhatmini calibrates the Geekservo to 500-2500us, so those are the
extremes. There's a deadband near 1500us where small offsets don't move
the motor — that's why `value(±1)` failed earlier.

Run on the Pi:  sudo python3 test_servo.py
"""
import time

from inventorhatmini import InventorHATMini, SERVO_1, SERVO_2

PORTS = [
    ("SERVO_1", SERVO_1),
    ("SERVO_2", SERVO_2),
]

# (pulse_width_us, label)
SPEEDS = [
    (1700, "slow forward"),
    (1900, "medium forward"),
    (2100, "fast forward"),
    (2500, "max forward"),
    (1500, "stop"),
    (1300, "slow reverse"),
    (1100, "medium reverse"),
    (900,  "fast reverse"),
    (500,  "max reverse"),
]

DURATION_S = 2.0

board = InventorHATMini()

for name, port in PORTS:
    print(f"\n=== {name} ===")
    servo = board.servos[port]
    servo.enable()

    for us, label in SPEEDS:
        print(f"  pulse({us}us) — {label}, {DURATION_S:g}s")
        servo.pulse(us)
        time.sleep(DURATION_S)

    servo.to_mid()
    servo.disable()

print("\nDone.")
