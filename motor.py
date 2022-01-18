#!/usr/bin/env python

import RPi.GPIO as GPIO
import math
import time
import sys
import json
from random import randint, random



class Speed():
    def next(self):
        pass


class General(Speed):
    def __init__(self, configFn):
        self.minDc = 12
        self.minF = 44
        self.maxF = 250
        with open(configFn, "r") as cf:
            js = json.load(cf)
            self.minDc = js["minDc"]

    def next(self, anythingBetween):
        i = anythingBetween(self.minF, self.maxF)
        dc = anythingBetween(self.minDc, 100)
        print(i, dc)
        return (i, dc)

class PitchBased(Speed):
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

    @staticmethod
    def freq(note):
        return math.pow(2, (note - 69) / 12.0) * 440
    
    def __init__(self, tonic):
        mode = [2, 2, 1, 2, 2, 1, 2]
        t = tonic - 12
        self.notes = [t] if not t < 44 else []
        for m in range(len(mode)):
            n = t + mode[m]
            if not n < 44 and not n > 52:
                self.notes.append(n)
            t = n
        print("using", self.notes)

    def next(self, anythingBetween):
        note = self.notes[anythingBetween(0, len(self.notes) - 1)]
        f = PitchBased.freq(note)
        dc = PitchBased.dcPerNote[note]
        print(note, f, dc)
        return (f, dc)


class DiscreteSpeedMotor():
    def __init__(self, speedSource: Speed):
        print("starting motor")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(12, GPIO.OUT)
        self.pwm = None
        self.speedSource = speedSource

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
        while True:
            (f, dc) = self.speedSource.next(randint)
            t = 2 + (8 * random())
            self.start(f, dc)
            time.sleep(t)

#DiscreteSpeedMotor(PitchBased(int(sys.argv[1]))).run()
DiscreteSpeedMotor(General(sys.argv[1] if len(sys.argv) > 1 else "../config.json")).run()
