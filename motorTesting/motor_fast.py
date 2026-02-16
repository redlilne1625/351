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
# Set to HIGH to reverse the previous direction
GPIO.output(DIR, GPIO.LOW) 

start_delay = 0.002
target_delay = 0.0003
current_delay = start_delay

try:
    print("Accelerating motor (reversed)...")
    while True:
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(current_delay)
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(current_delay)
        
        if current_delay > target_delay:
            current_delay -= 0.000005 

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nStopped.")
