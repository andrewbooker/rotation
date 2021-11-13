#!/usr/bin/env python

import RPi.GPIO as GPIO
import math
import time
import sys
from random import randint, random

dcPerNote = {
	44: 12,
	45: 13,
	46: 14,
	47: 16,
	48: 18,
	49: 21,
	50: 28,
	51: 46,
	52: 100
}


class DiscretePitchMotor():
	@staticmethod
	def freq(note):
		return math.pow(2, (note - 69) / 12.0) * 440

	def __init__(self):
		print("starting motor")
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(12, GPIO.OUT)
		self.pwm = None

	def __del__(self):
		self.stop()
		GPIO.cleanup()
		print("motor stopped")

	def start(self, f, dc):
		if self.pwm is None:
			self.pwm = GPIO.PWM(12, f)
			self.pwm.start(dc)
		else:
			self.pwm.ChangeFrequency(f)
			self.pwm.ChangeDutyCycle(dc)

	def stop(self):
		if self.pwm is not None:
			self.pwm.stop()

	def run(self):
		notes = [44, 46, 47, 49, 51]
		while True:
			note = notes[randint(0, len(notes) - 1)]
			f = DiscretePitchMotor.freq(note)
			dc = dcPerNote[note]
			t = 2 + (3 * random())
			self.start(f, dc)
			print(note, f, dc, t)
			time.sleep(t)


class Motor():
	def __init__(self):
		print("starting motor")
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(12, GPIO.OUT)
		self.pwm = GPIO.PWM(12, 100)

	def __del__(self):
		self.pwm.stop()
		GPIO.cleanup()
		print("motor stopped")

	def startAt(self, dc):
		self.pwm.start(dc)
		while True:
			time.sleep(1.0)

	def run(self):
		mi = 20
		ma = 100

		self.startAt(mi + ((ma - mi) / 2))
		start = time.time()
		while True:
			t = time.time() - start
			time.sleep(0.01)
			v = mi + ((ma - mi) * (0.5 + (0.5 * math.sin(t / 3))))
			self.pwm.ChangeDutyCycle(v)

#Motor().run()
#Motor().startAt(int(sys.argv[2]))
DiscretePitchMotor().run()
