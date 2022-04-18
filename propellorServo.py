#!/usr/bin/env python

import RPi.GPIO as GPIO
import random


FREQ_HZ = 50
MIN = 1.8
MAX = 9.8

GPIO.setmode(GPIO.BCM)

def anythingBetween(mi, ma):
    return mi + ((ma - mi) * random.random())

class Device():
    def __init__(self, description, channel):
        self.desc = description
        print("starting", self.desc)
        GPIO.setup(channel, GPIO.OUT)
        self.pwm = GPIO.PWM(channel, FREQ_HZ)
        self.pwm.start(0)
        self.value = 0

    def __del__(self):
        self.stop()
        GPIO.cleanup()
        print(self.desc, "stopped")

    def set(self, dc):
        self.value = dc
        print(self.desc, "%0.2f" % dc)
        self.pwm.ChangeDutyCycle(dc)

    def stop(self):
        if self.pwm is not None:
            self.pwm.stop()


servo = Device("servo", 2)

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


def startServer():
    HTTPServer(("0.0.0.0", PORT), Controller).serve_forever()

import time
import threading


server = threading.Thread(target=startServer, args=(), daemon=False)
server.start()
print("serving on port", PORT)


while True:
    time.sleep(5)
    servo.set(anythingBetween(MIN, MAX))

del servo
server.join()
