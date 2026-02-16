import RPi.GPIO as GPIO
import time

PUL = 17
DIR = 27
ENA = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

GPIO.output(ENA, GPIO.LOW)
# Changed from GPIO.LOW to GPIO.HIGH to reverse direction
GPIO.output(DIR, GPIO.HIGH) 

# Start slow and ramp up to avoid the "wiggle"
start_delay = 0.002    # Slow start
target_delay = 0.0003  # Fast target speed
current_delay = start_delay

try:
    print("Accelerating motor in reverse...")
    while True:
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(current_delay)
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(current_delay)
        
        # Gradually decrease delay (speed up) until target is reached
        if current_delay > target_delay:
            current_delay -= 0.000005 

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nStopped.")
