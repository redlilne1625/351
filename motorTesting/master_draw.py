import RPi.GPIO as GPIO
import time
import math
import json
import os

# --- LOAD CALIBRATION ---
CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    print("ERROR: config.json not found! Run 'python3 calibrate.py' first.")
    exit()

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

STEPS_PER_MM_X = config['steps_per_mm_x']
STEPS_PER_MM_Y = config['steps_per_mm_y']
MAX_X = config['width_mm']
MAX_Y = config['height_mm']

print(f"Loaded Config: Grid is {MAX_X}mm x {MAX_Y}mm")

# --- PINS ---
PIN_X_PUL = 17
PIN_X_DIR = 27
PIN_X_ENA = 22
PIN_Y_PUL = 24
PIN_Y_DIR = 25
PIN_Y_ENA = 5

DRAW_SPEED = 0.001

# --- TRACKING ---
current_x_steps = 0
current_y_steps = 0

# --- SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for p in [PIN_X_PUL, PIN_X_DIR, PIN_X_ENA, PIN_Y_PUL, PIN_Y_DIR, PIN_Y_ENA]:
    GPIO.setup(p, GPIO.OUT)

# --- CORE MOVEMENT ---
def step_motor(pul, dir_pin, direction):
    GPIO.output(dir_pin, direction)
    GPIO.output(pul, GPIO.HIGH)
    time.sleep(DRAW_SPEED)
    GPIO.output(pul, GPIO.LOW)
    time.sleep(DRAW_SPEED)

def goto_mm(target_x, target_y):
    global current_x_steps, current_y_steps
    
    # Convert mm to steps
    tx = int(target_x * STEPS_PER_MM_X)
    ty = int(target_y * STEPS_PER_MM_Y)
    
    dx = tx - current_x_steps
    dy = ty - current_y_steps
    
    dir_x = 1 if dx > 0 else 0
    dir_y = 1 if dy > 0 else 0
    
    dx = abs(dx)
    dy = abs(dy)
    
    # Bresenham's Line Algorithm
    steps = max(dx, dy)
    accum_x = dx / 2.0
    accum_y = dy / 2.0
    
    for i in range(steps):
        accum_x -= dx
        accum_y -= dy
        if accum_x < 0:
            accum_x += steps
            step_motor(PIN_X_PUL, PIN_X_DIR, dir_x)
            current_x_steps += (1 if dir_x == 1 else -1)
        if accum_y < 0:
            accum_y += steps
            step_motor(PIN_Y_PUL, PIN_Y_DIR, dir_y)
            current_y_steps += (1 if dir_y == 1 else -1)

# --- SHAPES ---
def draw_rect(x, y, w, h):
    print(f"Drawing Rect at {x},{y}")
    goto_mm(x, y) # Bottom Left
    goto_mm(x + w, y) # Bottom Right
    goto_mm(x + w, y + h) # Top Right
    goto_mm(x, y + h) # Top Left
    goto_mm(x, y) # Close

def draw_circle(cx, cy, r):
    print(f"Drawing Circle center {cx},{cy}")
    segments = 72
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        goto_mm(px, py)

# --- EXECUTION ---
try:
    # 1. Draw a test border
    draw_rect(10, 10, 50, 50) # Draw 50mm square
    
    # 2. Draw a circle in the middle of the grid
    mid_x = MAX_X / 2
    mid_y = MAX_Y / 2
    draw_circle(mid_x, mid_y, 25) # 25mm radius circle
    
    # 3. Go Home
    goto_mm(0, 0)
    print("Done!")

except KeyboardInterrupt:
    print("Stopped.")
finally:
    GPIO.cleanup()
