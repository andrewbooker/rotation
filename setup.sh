#!/bin/bash

sudo killall wpa_supplicant
sudo ./setup.py $1 $2
sudo wpa_supplicant -B -c /etc/wpa_supplicant/wpa_supplicant.conf -i wlan0 -Dnl80211,wext
