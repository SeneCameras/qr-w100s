import socket
import sys
import cv2
import binascii
import struct

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

on = [ 0x60, 0x00, throttle, 0x00, rotation, 0x00, elev, 0x00, aile,
        0x00, aile, 0x00, throttle, 0x00, rotation, 0x00, elev]
on.append( (sum(on)) & 0xff )
on=struct.pack("18B",*tuple(on))

data = on
sock.send(on)
while(turnedon):

    key = cv2.waitKey(30)
    if key == 119:
        sock.send(off)
    if key ==27:
        exit(0)

sock.close()
