import RPi.GPIO as GPIO
import time

# Y AXIS
Y_PUL = 17
Y_DIR = 27
Y_ENA = 22

# X AXIS
X_PUL = 23
X_DIR = 24
X_ENA = 25

DELAY = 0.0003
STEPS = 3000

GPIO.setmode(GPIO.BCM)

# Setup
for pin in [Y_PUL, Y_DIR, Y_ENA, X_PUL, X_DIR, X_ENA]:
    GPIO.setup(pin, GPIO.OUT)

# Enable
GPIO.output(Y_ENA, GPIO.LOW)
GPIO.output(X_ENA, GPIO.LOW)

# ✅ Your calibrated directions
GPIO.output(X_DIR, GPIO.LOW)
GPIO.output(Y_DIR, GPIO.HIGH)

try:
    for i in range(STEPS):
        GPIO.output(X_PUL, GPIO.HIGH)
        GPIO.output(Y_PUL, GPIO.HIGH)
        time.sleep(DELAY)

        GPIO.output(X_PUL, GPIO.LOW)
        GPIO.output(Y_PUL, GPIO.LOW)
        time.sleep(DELAY)

    print("Diagonal movement complete 🚀")

except KeyboardInterrupt:
    print("Stopped")

finally:
    GPIO.cleanup()
