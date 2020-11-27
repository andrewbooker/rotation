#!/usr/bin/env python

import RPi.GPIO as GPIO
import math
import time

class Motor():
	def __init__(self):
		print("starting motor")
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(12, GPIO.OUT)
		self.pwm = GPIO.PWM(12, 200)

	def __del__(self):
		self.pwm.stop()
		GPIO.cleanup()
		print("motor stopped")

	def run(self):
		mi = 20
		ma = 80

		self.pwm.start(mi + ((ma - mi) / 2))
		start = time.time()
		while True:
			t = time.time() - start
			time.sleep(0.01)
			v = mi + ((ma - mi) * (0.5 + (0.5 * math.sin(t / 3))))
			self.pwm.ChangeDutyCycle(v)

Motor().run()
