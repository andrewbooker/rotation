#!/usr/bin/env python

import sys
import os
import json

def config(item):
    with open(sys.argv[2]) as conf:
        c = json.load(conf)
        return c[item]

def writeCnx(prefix):
    ssid = config("%s_ssid" % prefix)
    psk = config("%s_psk" % prefix)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as wpa:
        wpa.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
        wpa.write("update_config=0\n")
        wpa.write("country=GB\n")
        wpa.write("\n")
        wpa.write("network={\n")
        wpa.write("\tssid=\"%s\"\n" % ssid)
        wpa.write("\tpsk=%s\n" % psk)
        wpa.write("\tpriority=1\n")
        wpa.write("}\n")

writeCnx(sys.argv[1])
