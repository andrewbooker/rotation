#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
FREQ_HZ = 50
MIN = 1.8
MAX = 9.8

GPIO.setmode(GPIO.BCM)

class Device():
    def __init__(self, description, channel):
        self.desc = description
        print("starting", self.desc)
        GPIO.setup(channel, GPIO.OUT)
        self.pwm = GPIO.PWM(channel, FREQ_HZ)
        self.pwm.start(0)

    def __del__(self):
        self.stop()
        GPIO.cleanup()
        print(self.desc, "stopped")

    def set(self, dc):
        self.pwm.ChangeDutyCycle(dc)

    def stop(self):
        if self.pwm is not None:
            self.pwm.stop()



s = Device("servo", 2)
time.sleep(5)
s.set(MIN)
print("at min")
time.sleep(5)
s.set(MAX)
print("at max")
time.sleep(5)

del s
