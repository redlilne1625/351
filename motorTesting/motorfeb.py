import RPi.GPIO as GPIO
import time

# ------------------------
# PIN CONFIGURATION (BCM)
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
TEST_DURATION = 5 # seconds

# ------------------------
# SETUP
# ------------------------

GPIO.setmode(GPIO.BCM)

# Setup Y
GPIO.setup(Y_PUL, GPIO.OUT)
GPIO.setup(Y_DIR, GPIO.OUT)
GPIO.setup(Y_ENA, GPIO.OUT)

# Setup X
GPIO.setup(X_PUL, GPIO.OUT)
GPIO.setup(X_DIR, GPIO.OUT)
GPIO.setup(X_ENA, GPIO.OUT)

# Enable drivers
GPIO.output(Y_ENA, GPIO.LOW)
GPIO.output(X_ENA, GPIO.LOW)

# Default direction
x_direction = GPIO.LOW
y_direction = GPIO.LOW

GPIO.output(X_DIR, x_direction)
GPIO.output(Y_DIR, y_direction)


# ------------------------
# FUNCTION TO MOVE MOTOR
# ------------------------

def run_motor(pul_pin, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        GPIO.output(pul_pin, GPIO.HIGH)
        time.sleep(DELAY)
        GPIO.output(pul_pin, GPIO.LOW)
        time.sleep(DELAY)


try:

    # ------------------------
    # TEST X AXIS
    # ------------------------

    print("\nTesting X axis for 5 seconds...")
    run_motor(X_PUL, TEST_DURATION)

    answer = input("Did X move in the correct direction? (y/n): ").strip().lower()

    if answer == "n":
        print("Flipping X direction...")
        x_direction = GPIO.HIGH if x_direction == GPIO.LOW else GPIO.LOW
        GPIO.output(X_DIR, x_direction)
    else:
        print("X direction kept.")

    # ------------------------
    # TEST Y AXIS
    # ------------------------

    print("\nTesting Y axis for 5 seconds...")
    run_motor(Y_PUL, TEST_DURATION)

    answer = input("Did Y move in the correct direction? (y/n): ").strip().lower()

    if answer == "n":
        print("Flipping Y direction...")
        y_direction = GPIO.HIGH if y_direction == GPIO.LOW else GPIO.LOW
        GPIO.output(Y_DIR, y_direction)
    else:
        print("Y direction kept.")

    print("\nCalibration complete ✅")
    print("X direction:", "HIGH" if x_direction else "LOW")
    print("Y direction:", "HIGH" if y_direction else "LOW")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.cleanup()
