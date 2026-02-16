import RPi.GPIO as GPIO
import time

PUL = 17   # change if needed
DIR = 27
ENA = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

GPIO.output(ENA, GPIO.LOW)      # enable driver
GPIO.output(DIR, GPIO.HIGH)     # direction

delay = 0.001  # speed (lower = faster)

try:
    while True:
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(delay)

except KeyboardInterrupt:
    GPIO.cleanup()
