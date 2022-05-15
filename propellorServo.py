#!/usr/bin/env python

import RPi.GPIO as GPIO
import random

FREQ_HZ = 50



class Ports():
    def __init__(self):
        print("initialising GPIO")
        GPIO.setmode(GPIO.BCM)
        self.ports = []

    def __del__(self):
        print("cleaning up GPIO ports")
        [p.stop() for p in self.ports]
        GPIO.cleanup()

    def newPwm(self, channel, freq):
        GPIO.setup(channel, GPIO.OUT)
        p = GPIO.PWM(channel, FREQ_HZ)
        self.ports.append(p)
        return p

    def newOutput(self, channel):
        GPIO.setup(channel, GPIO.OUT, initial=0)

ports = Ports()

def anythingBetween(mi, ma):
    return mi + ((ma - mi) * random.random())

class Device():
    def __init__(self, description, channel):
        self.desc = description
        print("starting", self.desc)
        self.pwm = ports.newPwm(channel, FREQ_HZ)
        self.pwm.start(0)
        self.value = 0

    def __del__(self):
        print(self.desc, "stopped")

    def set(self, dc):
        self.value = dc
        print(self.desc, "%0.2f" % dc)
        self.pwm.ChangeDutyCycle(dc)

import time
class RandomValueProvider():
    def __init__(self, min, max, interval):
        self.min = min
        self.max = max
        self.interval = interval
        self.val = min + ((max - min) / 2.0)
        self.start = 0
        self.__resetTime()

    def __resetTime(self):
        self.start = time.time() + self.interval

    def get(self):
        if time.time() > self.start:
            self.val = anythingBetween(self.min, self.max)
            self.__resetTime()
        return self.val


import threading

class Servo(Device):
    MIN = 2.3
    MAX = 9.3
    MID = 0.5 * (MAX + MIN)

    def __init__(self):
        Device.__init__(self, "servo", 10)
        self.manual = threading.Event()
        self.valueProvider = RandomValueProvider(Servo.MIN, Servo.MAX, 5.13)

    def run(self):
        while True:
            if not self.manual.is_set():
                v = self.valueProvider.get()
                if v != self.value:
                    self.set(v)
            time.sleep(0.05)

    def toRandom(self):
        self.manual.clear()

    def toManual(self):
        if self.manual.is_set():
            return
        self.manual.set()
        self.set(Servo.MID)

class InertServo():
	def __init__(self):
		self.value = 0
	def toRandom(self):
		pass
	def toManual(self):
		pass
	def set(self, ignore):
		pass

class Propellor(Device):
    MIN = 2.3
    MAX = 8
    MID = 0.5 * (MAX + MIN)
    PIN_DIR = 9
    PIN_SPEED = 11

    def __init__(self):
        Device.__init__(self, "propellor", Propellor.PIN_SPEED)
        self.isReversing = False
        self.manual = threading.Event()
        ports.newOutput(Propellor.PIN_DIR)
        GPIO.output(Propellor.PIN_DIR, 0)
        self.valueProvider = RandomValueProvider(Propellor.MIN, Propellor.MAX, 2.37)

    def run(self):
        while True:
            if not self.manual.is_set():
                v = self.valueProvider.get()
                if v != self.value:
                    if random.random() > 0.7:
                        self._toggleDirection()
                    self.set(v)
            time.sleep(0.05)

    def toRandom(self):
        self.ahead()
        self.manual.clear()

    def stop(self):
        self.manual.set()
        self.set(0)

    def _toggleDirection(self):
        self.set(0)
        time.sleep(0.1)
        self.isReversing = not self.isReversing
        GPIO.output(Propellor.PIN_DIR, 1 if self.isReversing else 0)
        time.sleep(0.1)

    def ahead(self):
        propellor.manual.set()
        if self.isReversing:
            self._toggleDirection()
        propellor.set(Propellor.MID)

    def toggleForwardReverse(self):
        propellor.manual.set()
        propellor._toggleDirection()
        self.set(Propellor.MID)

import sys
isPilot = int(sys.argv[1]) if len(sys.argv) > 1 else 0

servo = Servo() if isPilot else InertServo()
propellor = Propellor()

PORT = 9977
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Controller(BaseHTTPRequestHandler):
    def __standardResponse(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.__standardResponse()
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.end_headers()

    def do_GET(self):
        self.__standardResponse()
        self.end_headers()
        payload = {
            "pos": servo.value,
            "speed": propellor.value,
            "isForward": not propellor.isReversing
        }
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _stop(self):
        propellor.stop()
        servo.toManual()
        servo.set(Servo.MID)

    def _left(self):
        servo.toManual()
        servo.set(Servo.MIN)

    def _right(self):
        servo.toManual()
        servo.set(Servo.MAX)

    def _ahead(self):
        servo.toManual()
        servo.set(Servo.MID)
        propellor.ahead()

    def _toggleForwardReverse(self):
        servo.toManual()
        servo.set(Servo.MID)
        propellor.toggleForwardReverse()

    def _random(self):
        servo.toRandom()
        propellor.toRandom()

    def do_POST(self):
        self.__standardResponse()
        self.end_headers()
        self.wfile.write(json.dumps({}).encode("utf-8"))

        getattr(self, "_%s" % self.path[1:])()


def startServer():
    HTTPServer(("0.0.0.0", PORT), Controller).serve_forever()


threads = []
threads.append(threading.Thread(target=startServer, args=(), daemon=True))
threads.append(threading.Thread(target=propellor.run, args=(), daemon=True))
if isPilot == 1:
    threads.append(threading.Thread(target=servo.run, args=(), daemon=True))

[t.start() for t in threads]
print("serving on port", PORT)

[t.join() for t in threads]
del ports
