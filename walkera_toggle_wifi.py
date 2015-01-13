import socket
import sys
import cv2
import binascii
import struct

# toggles the wifi control of the qr w100s
# 'w' turns the wifi control on
# 's' turns the wifi control off

turnedon = False
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock = socket.socket()
sock.connect(("192.168.10.1", 2001))
turnedon = True


throttle = 0x01
rotation = 0x7f
elev = 0x7f
aile =  0x7f

off = [ 0x60, 0x00, throttle, 0x00, rotation, 0x00, elev, 0x00, aile,
        0x00, aile, 0x00, throttle, 0x00, rotation, 0x00, elev]
off.append( (sum(off)) & 0xff )
off=struct.pack("18B",*tuple(off))

on = [ 0x61, 0x00, throttle, 0x00, rotation, 0x00, elev, 0x00, aile,
        0x00, aile, 0x00, throttle, 0x00, rotation, 0x00, elev]
on.append( (sum(on)) & 0xff )
on=struct.pack("18B",*tuple(on))

while(turnedon):
	sock.send(on)
	# key = cv2.waitKey(30)
    # if key == ord('w'):
    #     sock.send(on)
    # if key == 115:
    #     sock.send(off)
    # if key ==27:
    #     exit(0)

sock.close()
