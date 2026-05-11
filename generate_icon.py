"""Generate the iOS apple-touch-icon — a classic Lego minifigure head.

Outputs static/apple-touch-icon.png at 180x180 (the canonical Retina
size — iOS scales it down for older devices). Re-run after tweaks.

  pip install Pillow
  python3 generate_icon.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "static", "apple-touch-icon.png")

SIZE = 180
SCALE = 4  # supersample for clean anti-aliasing
W = SIZE * SCALE

BG = (17, 17, 17)            # #111 — app's dark theme
YELLOW = (254, 216, 48)      # classic Lego yellow
BLACK = (10, 10, 10)

img = Image.new("RGB", (W, W), BG)
draw = ImageDraw.Draw(img)

center_x = W // 2

# --- Stud (small cylinder on top of the head) ---
stud_w = int(W * 0.22)
stud_h = int(W * 0.13)
stud_x = (W - stud_w) // 2
stud_y = int(W * 0.09)
stud_r = int(stud_w * 0.35)
draw.rounded_rectangle(
    (stud_x, stud_y, stud_x + stud_w, stud_y + stud_h),
    radius=stud_r,
    fill=YELLOW,
)

# --- Head (cylinder, drawn as rounded rectangle from the front) ---
head_w = int(W * 0.62)
head_h = int(W * 0.72)
head_x = (W - head_w) // 2
head_y = int(W * 0.20)  # slight overlap with stud — no visible seam
head_r = int(head_w * 0.22)
draw.rounded_rectangle(
    (head_x, head_y, head_x + head_w, head_y + head_h),
    radius=head_r,
    fill=YELLOW,
)

# --- Eyes (two black dots, upper-third of head) ---
eye_r = int(W * 0.038)
eye_y = head_y + int(head_h * 0.32)
eye_dx = int(head_w * 0.22)
for sign in (-1, 1):
    ex = center_x + sign * eye_dx
    draw.ellipse(
        (ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r),
        fill=BLACK,
    )

# --- Smile (lower half of an ellipse — arc from 0° to 180°) ---
mouth_w = int(W * 0.30)
mouth_h = int(W * 0.16)
mouth_x = center_x - mouth_w // 2
mouth_y = head_y + int(head_h * 0.50)
draw.arc(
    (mouth_x, mouth_y, mouth_x + mouth_w, mouth_y + mouth_h),
    start=0,
    end=180,
    fill=BLACK,
    width=int(W * 0.022),
)

# Downsample to final size with high-quality filter
img = img.resize((SIZE, SIZE), Image.LANCZOS)
img.save(OUT, "PNG")
print(f"Wrote {OUT} ({SIZE}x{SIZE})")
