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
import threading

class Servo(Device):
    MIN = 1.8
    MAX = 9.8

    def __init__(self):
        Device.__init__(self, "servo", 2)
        self.aheadOnly = threading.Event()

    def run(self):
        while not self.aheadOnly.is_set():
            time.sleep(5)
            self.set(anythingBetween(Servo.MIN, Servo.MAX))

        self.set(Servo.MIN)

class Propellor(Device):
    MIN = 2.3
    MAX = 10
    PIN_DIR = 3
    PIN_SPEED = 4

    def __init__(self):
        Device.__init__(self, "propellor", Propellor.PIN_SPEED)
        self.full = threading.Event()
        ports.newOutput(Propellor.PIN_DIR)
        GPIO.output(Propellor.PIN_DIR, 1)

    def run(self):
        while not self.full.is_set():
            sp = anythingBetween(Propellor.MIN, Propellor.MAX)
            time.sleep(1.0 + Propellor.MAX - sp)
            self.set(sp)

        self.set(Propellor.MAX)

servo = Servo()
propellor = Propellor()

PORT = 9977
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Controller(BaseHTTPRequestHandler):
    def _standardResponse(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "null")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self._standardResponse()
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.end_headers()

    def do_GET(self):
        self._standardResponse()
        self.end_headers()
        payload = {"pos": servo.value}
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_POST(self):
        self._standardResponse()
        self.end_headers()
        servo.aheadOnly.set()


def startServer():
    HTTPServer(("0.0.0.0", PORT), Controller).serve_forever()


threads = []
threads.append(threading.Thread(target=startServer, args=(), daemon=True))
threads.append(threading.Thread(target=propellor.run, args=(), daemon=True))
threads.append(threading.Thread(target=servo.run, args=(), daemon=True))

[t.start() for t in threads]
print("serving on port", PORT)

[t.join() for t in threads]
del ports
