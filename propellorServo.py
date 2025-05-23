#!/usr/bin/env python

import RPi.GPIO as GPIO
import random
import math

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
        p = GPIO.PWM(channel, freq)
        self.ports.append(p)
        return p

    def newOutput(self, channel):
        GPIO.setup(channel, GPIO.OUT, initial=0)

ports = Ports()

def anythingBetween(mi, ma):
    return mi + ((ma - mi) * random.random())

class Device():
    def __init__(self, description, channel, freq):
        self.desc = description
        print("starting", self.desc)
        self.pwm = ports.newPwm(channel, freq)
        self.pwm.start(0)
        self.value = 0

    def __del__(self):
        print(self.desc, "stopped")

    def set(self, dc):
        self.value = dc
        print(self.desc, "%0.2f" % dc)
        self.pwm.ChangeDutyCycle(dc)

    def isRunning(self):
        return self.value > 0

import time
class RandomValueProvider():
    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.interval = 9.9
        self.val = min + ((max - min) / 2.0)
        self.start = 0
        self.__resetTime()

    def __resetTime(self):
        self.interval = anythingBetween(3, 13)
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
    def isRunning(self):
        return False


class Propellor(Device):
    MIN = 10
    MAX = 100

    def __init__(self, pinSpeed, pinDir, freq):
        Device.__init__(self, "propellor", pinSpeed, freq)
        self.pinDir = pinDir
        self.isReversing = False
        self.manual = threading.Event()
        self.lock = threading.Lock()
        self.manual.set()
        ports.newOutput(pinDir)
        GPIO.output(pinDir, 0)
        self.cruise = 0.67 * Propellor.MAX
        self.valueProvider = RandomValueProvider(Propellor.MIN, self.cruise)

    def run(self):
        while True:
            if not self.manual.is_set():
                v = self.valueProvider.get()
                if v != self.value:
                    self._setDirection(not self.isReversing)
                    time.sleep(2.0)
                    self._setSpeedTo(v)
            time.sleep(0.05)

    def toRandom(self):
        self.ahead()
        self.manual.clear()

    def stop(self):
        self.manual.set()
        if self.isReversing:
            self._setDirection(False)

        self.set(0)
        time.sleep(0.1)

    def incrCruise(self):
        self.cruise = min(self.cruise + 5, Propellor.MAX)
        if self.manual.is_set() and self.value != 0:
            self._setSpeedTo(self.cruise)
        self.valueProvider.setMax(self.cruise)

    def decrCruise(self):
        self.cruise = max(self.cruise - 5, Propellor.MIN)
        if self.manual.is_set():
            self._setSpeedTo(self.cruise)
        self.valueProvider.setMax(self.cruise)

    def _setSpeedTo(self, s):
        self.lock.acquire()
        self.set(s)
        self.lock.release()

    def _setDirection(self, isReversing):
        print("setting direction to", "reverse" if isReversing else "forward")
        self.lock.acquire()
        self.set(0)
        time.sleep(0.1)
        self.isReversing = isReversing
        GPIO.output(self.pinDir, 1 if self.isReversing else 0)
        time.sleep(0.1)
        self.lock.release()

    def ahead(self):
        self.manual.set()
        if self.isReversing:
            self._setDirection(False)
        self._setSpeedTo(self.cruise)

    def reverse(self):
        self.manual.set()
        if not self.isReversing:
            self._setDirection(True)
        self._setSpeedTo(self.cruise)

import sys
isPilot = int(sys.argv[1]) if len(sys.argv) > 1 else 0
note = int(sys.argv[2]) if len(sys.argv) > 2 else 57
freq = math.pow(2, (n - 69)/12.0) * 220
propSideways = Propellor(11, 9, freq)
propFwdRev = Propellor(22, 27, freq) if isPilot else StubPropellor()
propellors = [propSideways, propFwdRev]


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
            "speedFwdRev": propFwdRev.value * (-1.0 if propFwdRev.isReversing else 1.0),
            "speedSideways": propSideways.value * (-1.0 if propSideways.isReversing else 1.0),
            "isForward": not propFwdRev.isReversing,
            "isClockwise": not propSideways.isReversing
        }
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _stop(self):
        [p.stop() for p in propellors]

    def _clockwise(self):
        propSideways.ahead()

    def _clockwiseStop(self):
        propSideways.stop()

    def _antiClockwise(self):
        propSideways.reverse()

    def _antiClockwiseStop(self):
        propSideways.stop()

    def _ahead(self):
        self._stop()
        propFwdRev.ahead()

    def _aheadStop(self):
        propFwdRev.stop()

    def _increase(self):
        for p in propellors:
            if p.isRunning():
                p.incrCruise()

    def _decrease(self):
        for p in propellors:
            if p.isRunning():
                p.decrCruise()

    def _reverse(self):
        if not propFwdRev.isReversing:
            propFwdRev.reverse()

    def _reverseStop(self):
        propFwdRev.stop()

    def _random(self):
        self._stop()
        propSideways.toRandom()

    def do_POST(self):
        self.__standardResponse()
        self.end_headers()
        self.wfile.write(json.dumps({}).encode("utf-8"))

        getattr(self, "_%s" % self.path[1:])()


def startServer():
    HTTPServer(("0.0.0.0", PORT), Controller).serve_forever()


threads = []
threads.append(threading.Thread(target=startServer, args=(), daemon=True))
threads.append(threading.Thread(target=propSideways.run, args=(), daemon=True))
if isPilot == 1:
    threads.append(threading.Thread(target=propFwdRev.run, args=(), daemon=True))

[t.start() for t in threads]
print("serving on port", PORT)

[t.join() for t in threads]
del ports
