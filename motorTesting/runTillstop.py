import RPi.GPIO as GPIO
import time

# ------------------------
# PIN CONFIG (BCM)
# ------------------------

# Y AXIS
Y_PUL = 17
Y_DIR = 27
Y_ENA = 22

# X AXIS
X_PUL = 23
X_DIR = 24
X_ENA = 25

DELAY = 0.0003

# ------------------------
# SETUP
# ------------------------

GPIO.setmode(GPIO.BCM)

for pin in [Y_PUL, Y_DIR, Y_ENA, X_PUL, X_DIR, X_ENA]:
    GPIO.setup(pin, GPIO.OUT)

# Enable drivers
GPIO.output(Y_ENA, GPIO.LOW)
GPIO.output(X_ENA, GPIO.LOW)

# ✅ Your calibrated directions
GPIO.output(X_DIR, GPIO.HIGH)
GPIO.output(Y_DIR, GPIO.LOW)

print("Running... Press CTRL+C to stop.")

try:
    while True:
        GPIO.output(X_PUL, GPIO.HIGH)
        GPIO.output(Y_PUL, GPIO.HIGH)
        time.sleep(DELAY)

        GPIO.output(X_PUL, GPIO.LOW)
        GPIO.output(Y_PUL, GPIO.LOW)
        time.sleep(DELAY)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.output(Y_ENA, GPIO.HIGH)  # Disable motors (optional)
    GPIO.output(X_ENA, GPIO.HIGH)
    GPIO.cleanup()
