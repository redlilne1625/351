import RPi.GPIO as GPIO
import time
import sys
import select
import tty
import termios

# --- CONFIGURATION ---
PUL = 17
DIR = 27
ENA = 22
DELAY = 0.0003
DATA_FILE = "x_data.txt"

# --- SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
GPIO.output(ENA, GPIO.LOW)
GPIO.output(DIR, GPIO.LOW) # Change to HIGH if moving wrong way

def is_key_pressed():
    """Checks if a key is waiting to be read without blocking"""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

print("\n--- X-AXIS MULTI-STEP SCANNER ---")
print(" [ENTER/SPACE] : Start or Pause (Records value)")
print(" [CTRL+C]      : Quit and Save FINAL value")
print("---------------------------------------------")

steps = 0
moving = False

# Save terminal settings
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)

try:
    tty.setcbreak(sys.stdin.fileno()) # Enable instant key reading

    while True:
        # 1. Check for Keypress
        if is_key_pressed():
            c = sys.stdin.read(1) # Clear the key buffer
            if moving:
                moving = False
                print(f"\n[PAUSED] Recorded Step Count: {steps}")
            else:
                moving = True
                print(f"\n[MOVING] ...")

        # 2. Move Motor if "moving" is True
        if moving:
            GPIO.output(PUL, GPIO.HIGH)
            time.sleep(DELAY)
            GPIO.output(PUL, GPIO.LOW)
            time.sleep(DELAY)
            steps += 1

except KeyboardInterrupt:
    print(f"\n\n[EXIT] Saving Final Value...")
    print(f"TOTAL X STEPS: {steps}")
    
    with open(DATA_FILE, "w") as f:
        f.write(str(steps))
    print(f"Saved to {DATA_FILE}")

finally:
    # Restore terminal settings so your cursor works again
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    GPIO.cleanup()
