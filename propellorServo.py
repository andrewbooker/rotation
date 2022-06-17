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

    def setMax(self, v):
        self.max = v

    def get(self):
        if time.time() > self.start:
            self.val = anythingBetween(self.min, self.max)
            self.__resetTime()
        return self.val


import threading


class StubPropellor():
    def __init__(self):
        self.value = 0
        self.isReversing = False
    def run(self):
        pass
    def toRandom(self):
        pass
    def stop(self):
        pass
    def incrCruise(self):
        pass
    def decrCruise(self):
        pass
    def ahead(self):
        pass
    def toggleForwardReverse(self):
        pass


class Propellor(Device):
    MIN = 5
    MAX = 100

    def __init__(self, randomInterval, pinSpeed, pinDir):
        Device.__init__(self, "propellor", pinSpeed)
        self.pinDir = pinDir
        self.isReversing = False
        self.manual = threading.Event()
        self.manual.set()
        ports.newOutput(pinDir)
        GPIO.output(pinDir, 0)
        self.cruise = 2 * Propellor.MIN
        self.valueProvider = RandomValueProvider(Propellor.MIN, self.cruise, randomInterval)

    def run(self):
        while True:
            if not self.manual.is_set():
                v = self.valueProvider.get()
                if v != self.value:
                    if random.random() > 0.5:
                        self._setDirection(not self.isReversing)
                    self.set(v)
            time.sleep(0.05)

    def toRandom(self):
        self.ahead()
        self.manual.clear()

    def stop(self):
        self.manual.set()
        if self.isReversing:
            self._setDirection(False)
        else:
            self.set(0)
            time.sleep(0.1)

    def incrCruise(self):
        self.cruise = min(self.cruise + 5, Propellor.MAX)
        if self.manual.is_set() and self.value != 0:
            self.set(self.cruise)
        self.valueProvider.setMax(self.cruise)

    def decrCruise(self):
        self.cruise = max(self.cruise - 5, Propellor.MIN)
        if self.manual.is_set():
            self.set(self.cruise)
        self.valueProvider.setMax(self.cruise)

    def _setDirection(self, isReversing):
        print("setting direction to", "reverse" if isReversing else "forward")
        self.set(0)
        time.sleep(0.1)
        self.isReversing = isReversing
        GPIO.output(self.pinDir, 1 if self.isReversing else 0)
        time.sleep(0.1)

    def ahead(self):
        self.manual.set()
        if self.isReversing:
            self._setDirection(False)
        self.set(self.cruise)

    def reverse(self):
        self.manual.set()
        if not self.isReversing:
            self._setDirection(True)
        self.set(self.cruise)

import sys
isPilot = int(sys.argv[1]) if len(sys.argv) > 1 else 0
randomInterval = float(sys.argv[2]) if len(sys.argv) > 2 else 8.37
propellorR = Propellor(randomInterval, 11, 9)
propellorL = Propellor(randomInterval, 22, 27) if isPilot else StubPropellor()
propellors = [propellorR, propellorL]


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
            "speedL": propellorL.value * (-1.0 if propellorL.isReversing else 1.0),
            "speedR": propellorR.value * (-1.0 if propellorR.isReversing else 1.0),
            "isForward": not propellorR.isReversing or not propellorL.isReversing
        }
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _stop(self):
        [p.stop() for p in propellors]

    def _left(self):
        propellorL.stop() # yes, this way round. to steer left, stop the left
        propellorR.ahead()

    def _right(self):
        propellorR.stop()
        propellorL.ahead()

    def _ahead(self):
        [p.ahead() for p in propellors]

    def _increase(self):
        [p.incrCruise() for p in propellors]

    def _decrease(self):
        [p.decrCruise() for p in propellors]

    def _reverse(self):
        if not propellorL.isReversing or not propellorR.isReversing:
            [p.reverse() for p in propellors]

    def _random(self):
        [p.toRandom() for p in propellors]

    def do_POST(self):
        self.__standardResponse()
        self.end_headers()
        self.wfile.write(json.dumps({}).encode("utf-8"))

        getattr(self, "_%s" % self.path[1:])()


def startServer():
    HTTPServer(("0.0.0.0", PORT), Controller).serve_forever()


threads = []
threads.append(threading.Thread(target=startServer, args=(), daemon=True))
threads.append(threading.Thread(target=propellorR.run, args=(), daemon=True))
if isPilot == 1:
    threads.append(threading.Thread(target=propellorL.run, args=(), daemon=True))

[t.start() for t in threads]
print("serving on port", PORT)

[t.join() for t in threads]
del ports
