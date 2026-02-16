import RPi.GPIO as GPIO
import time

# -----------------------------
# GPIO PIN SETUP
# -----------------------------
PUL = 17   # PUL-  (step)
DIR = 27   # DIR-  (direction)
ENA = 22   # ENA-  (enable)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

# -----------------------------
# ENABLE DRIVER
# -----------------------------
GPIO.output(ENA, GPIO.LOW)   # LOW = enabled on most drivers

# -----------------------------
# SET DIRECTION
# -----------------------------
GPIO.output(DIR, GPIO.HIGH)  # HIGH = one direction, LOW = reverse

# -----------------------------
# CONTINUOUS ROTATION LOOP
# -----------------------------
delay = 0.0005   # speed (lower = faster)

print("Motor spinning continuously... Press CTRL+C to stop.")

try:
    while True:
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(delay)

except KeyboardInterrupt:
    print("Stopping motor...")

finally:
    GPIO.cleanup()
