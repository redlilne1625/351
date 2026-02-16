import RPi.GPIO as GPIO
import time
import threading

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

GPIO.output(Y_ENA, GPIO.LOW)
GPIO.output(X_ENA, GPIO.LOW)

# Your calibrated "forward"
X_FORWARD = GPIO.LOW
Y_FORWARD = GPIO.HIGH

moving = False
current_motor = None
current_direction = None


# ------------------------
# MOTOR THREAD
# ------------------------

def motor_runner():
    global moving
    while True:
        if moving:
            GPIO.output(current_motor, GPIO.HIGH)
            time.sleep(DELAY)
            GPIO.output(current_motor, GPIO.LOW)
            time.sleep(DELAY)
        else:
            time.sleep(0.01)


thread = threading.Thread(target=motor_runner, daemon=True)
thread.start()

print("""
Manual Homing Control
---------------------
x  -> X forward
X  -> X backward
y  -> Y forward
Y  -> Y backward
s  -> Stop
q  -> Quit
""")

try:
    while True:
        cmd = input("Enter command: ").strip()

        if cmd == "x":
            GPIO.output(X_DIR, X_FORWARD)
            current_motor = X_PUL
            moving = True

        elif cmd == "X":
            GPIO.output(X_DIR, not X_FORWARD)
            current_motor = X_PUL
            moving = True

        elif cmd == "y":
            GPIO.output(Y_DIR, Y_FORWARD)
            current_motor = Y_PUL
            moving = True

        elif cmd == "Y":
            GPIO.output(Y_DIR, not Y_FORWARD)
            current_motor = Y_PUL
            moving = True

        elif cmd == "s":
            moving = False
            print("Stopped.")

        elif cmd == "q":
            break

except KeyboardInterrupt:
    pass

finally:
    moving = False
    GPIO.output(Y_ENA, GPIO.HIGH)
    GPIO.output(X_ENA, GPIO.HIGH)
    GPIO.cleanup()
    print("Exited safely.")
