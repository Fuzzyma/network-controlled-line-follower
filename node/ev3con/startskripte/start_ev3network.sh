#!/bin/bash

pw=NICHTINGITHUB!!!
iface=wlan0
essid=ev3network
channel=9

# Fahrzeugnummer laut Klebezettel:
nr=1

echo $pw | sudo -S ifconfig $iface down
sudo iwconfig $iface mode Ad-hoc essid $essid channel $channel key off
sudo ifconfig $iface up
sudo ifconfig $iface "10.42.1.1$nr"

sleep 2
