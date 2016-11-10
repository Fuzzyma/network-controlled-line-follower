# python-ev3con

A student-project in communication systems at TU Dresden.

## Howto run the scripts?

To run the scripts for connected driving, you have to start the WLAN connection first. Start ```start_ev3network.sh``` (to be found in the user folder ev3con) out of BRICKMAN with a click on the middle button. If an error occurs telling you that the interface ```wlan0``` cannot be found, just remove the WLAN-Stick, plug it in again and try it once more.

After that, you can start either ```start_af_hopbyhop.sh``` or ```start_af_platooning.sh``` the same way. The car number doesn't indicate, in which order the convoy is built up. The first car you start will be the first car in the convoy and so on. Please note that it would be a good idea to wait with starting a second Brick until the first one begins to show some output on the screen.

The scripts automatically start in idle mode, so you have to manually send a START command via Broadcast (10.255.255.255) which means you need a laptop with a connection to the built up Ad-hoc network.

```bash
sudo ifconfig wlan1 down
sudo iwconfig wlan1 mode Ad-hoc essid ev3network channel 8 key off
sudo ifconfig wlan1 up
sudo ifconfig wlan1 10.42.1.x
```

The command can be sent with a script in this repository.

```bash
python ./wlan/wlan_sender.py -ip 10.255.255.255 -m START
```

You can also send STOP and QUIT.

For driving along the line without network connection, just start ```start_af.py``` with the Brickman, the car should begin to drive immediately.

Feel free to connect via USB cable and ssh, but be sure to modify the newly created connection to share your internet with the brick to be able to do downloads und updates.

The standard IPs are 10.42.0.1x in USB-Mode and 10.42.1.1x with WLAN where x is the car number.

```ssh ev3con@10.42.0.13``` would connect you via USB to the third car, if possible.

It is perfectly possible to look at the network traffic with a program like wireshark or kismet for debugging purposes!

Author: Patrick Ziegler
