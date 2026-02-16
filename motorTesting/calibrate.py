import RPi.GPIO as GPIO
import time
import sys
import tty
import termios
import json

# --- FILE TO SAVE RESULTS ---
CONFIG_FILE = "config.json"

# --- PIN MAP (TB6600) ---
# Swapped X and Y pins as requested
PIN_X_PUL = 24
PIN_X_DIR = 25
PIN_X_ENA = 5
PIN_Y_PUL = 17
PIN_Y_DIR = 27
PIN_Y_ENA = 22

# --- SETTINGS ---
CALIBRATION_SPEED = 0.001
JOG_SPEED = 0.002  # Slower speed for manual jog
DIR_FORWARD = 1
DIR_BACKWARD = 0

# --- SETUP GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pins = [PIN_X_PUL, PIN_X_DIR, PIN_X_ENA, PIN_Y_PUL, PIN_Y_DIR, PIN_Y_ENA]
for p in pins:
    GPIO.setup(p, GPIO.OUT)
    GPIO.output(p, 0) # Initialize low

# --- HELPER FUNCTIONS ---
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def step_motor(pul, dir_pin, direction, delay):
    GPIO.output(dir_pin, direction)
    GPIO.output(pul, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(pul, GPIO.LOW)
    time.sleep(delay)

def scan_axis(name, pul, dir_pin):
    print(f"\nScanning {name} Axis. Press CTRL+C immediately when it hits the end.")
    input(f"Press Enter to start {name}...")
    steps = 0
    try:
        while True:
            step_motor(pul, dir_pin, DIR_FORWARD, CALIBRATION_SPEED)
            steps += 1
    except KeyboardInterrupt:
        print(f"STOPPED. {name} steps: {steps}")
    return steps

def manual_jog():
    print("\n--- MANUAL JOG MODE ---")
    print("WASD to move. Q to Set Home (0,0) and Start Scan.")
    while True:
        k = get_key()
        if k == 'q': break
        if k == 'd': step_motor(PIN_X_PUL, PIN_X_DIR, DIR_FORWARD, JOG_SPEED)
        if k == 'a': step_motor(PIN_X_PUL, PIN_X_DIR, DIR_BACKWARD, JOG_SPEED)
        if k == 'w': step_motor(PIN_Y_PUL, PIN_Y_DIR, DIR_FORWARD, JOG_SPEED)
        if k == 's': step_motor(PIN_Y_PUL, PIN_Y_DIR, DIR_BACKWARD, JOG_SPEED)

# --- MAIN LOGIC ---
try:
    print("=== STEP 1: JOG TO START ===")
    manual_jog()

    print("\n=== STEP 2: SCAN AXES ===")
    x_steps = scan_axis("X", PIN_X_PUL, PIN_X_DIR)
    time.sleep(1)
    y_steps = scan_axis("Y", PIN_Y_PUL, PIN_Y_DIR)

    print("\n=== STEP 3: PHYSICAL MEASUREMENT ===")
    x_mm = float(input(f"We counted {x_steps} steps for X. How long is this in mm? "))
    y_mm = float(input(f"We counted {y_steps} steps for Y. How long is this in mm? "))

    # Calculate Resolution
    res_x = x_steps / x_mm
    res_y = y_steps / y_mm

    data = {
        "max_steps_x": x_steps,
        "max_steps_y": y_steps,
        "steps_per_mm_x": res_x,
        "steps_per_mm_y": res_y,
        "width_mm": x_mm,
        "height_mm": y_mm
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

    print(f"\nSUCCESS! Calibration saved to {CONFIG_FILE}")
    print(f"X Res: {res_x:.2f} steps/mm | Y Res: {res_y:.2f} steps/mm")

except Exception as e:
    print(e)
finally:
    GPIO.cleanup()
