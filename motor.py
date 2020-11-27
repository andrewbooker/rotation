#!/usr/bin/env python

import RPi.GPIO as GPIO
import math

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
pwm = GPIO.PWM(12, 200)

mi = 20
ma = 80
pwm.start(mi + ((ma - mi) / 2))

import time
start = time.time()

done = False
while not done:
	t = time.time() - start
	time.sleep(0.5)
	v = mi + ((ma - mi) * (0.5 + (0.5 * math.sin(t / 3))))
	pwm.ChangeDutyCycle(v)
	done = t > 60

pwm.stop()
GPIO.cleanup()
