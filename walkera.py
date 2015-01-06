import cv2
import numpy as np
import urllib
import socket
import sys
import struct
import binascii
from Tkinter import *

# opens the video stream
stream=urllib.urlopen('http://192.168.10.1:8080/?action=stream')
bytes=''

# 
switch = 0x61
throttle = 0x01
rotation = 0x7f
elev = 0x7f
aile =  0x7f

off = [ 0x60, 0x00, throttle, 0x00, rotation, 0x00, elev, 0x00, aile,
        0x00, aile, 0x00, throttle, 0x00, rotation, 0x00, elev]
off.append( (sum(off)) & 0xff )
off=struct.pack("18B",*tuple(off))

data = bytearray(18)

sock = socket.socket()
sock.connect(("192.168.10.1", 2001))

def update(data):
    # data[0] = 0x61
    data[0] = switch
    data[1] = throttle >> 8
    data[2] = throttle
    data[3] = rotation >> 8
    data[4] = rotation
    data[5] = elev >> 8
    data[6] = elev
    data[7] = aile >> 8
    data[8] = aile
    data[9] = aile >> 8
    data[10] = aile
    data[11] = throttle >> 8
    data[12] = throttle
    data[13] = rotation >> 8
    data[14] = rotation
    data[15] = elev >> 8
    data[16] = elev
    data[17] = sum(data[0:17]) & 0xFF
    return data

while True:
    data = update(data) 
    key = cv2.waitKey(1)
    if key ==27:
        exit(0)
    if key == 119:
        throttle = (throttle + 10)

    sock.send(data) 
    print binascii.hexlify(data)
    # sock.send(data)

    bytes+=stream.read(1080)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:
        jpg = bytes[a:b+2]
        bytes= bytes[b+2:]
        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
        if frame!= None:
			cv2.imshow('authenticated cam',frame)
        key = cv2.waitKey(1)

    	if key ==27:
    	    exit(0)
        # if key == 119:
        #     sock.send(off)
            # throttle = (throttle + 10) & 0xFF
        if key == 115 and throttle > 1:
            sock.send(data)
            # throttle -= 10

        root.after(25) 

root.mainloop()

sock.send(off)
sock.close()
