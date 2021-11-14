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

	def __init__(self, tonic):
		print("starting motor")
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(12, GPIO.OUT)
		self.pwm = None
		self.tonic = tonic

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
		mode = [1, 2, 2, 2, 1, 2, 1]
		t = self.tonic
		notes = [t] if not t < 44 else []
		for m in range(len(mode)):
			n = t + mode[m]
			if not n < 44 and not n > 52:
				notes.append(n)
			t = n

		print("using", notes)
		while True:
			note = notes[randint(0, len(notes) - 1)]
			f = DiscretePitchMotor.freq(note)
			dc = dcPerNote[note]
			t = 2 + (8 * random())
			self.start(f, dc)
			print(note, f, dc, t)
			time.sleep(t)

DiscretePitchMotor(int(sys.argv[1])).run()
